import uuid
import os
import logging
import functools
from dotenv import load_dotenv
load_dotenv()

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from .agent import graph

app = FastAPI(title="Corvus Chatbot API")

from .api.conversations import router as conversations_router
app.include_router(conversations_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


# ── Health checks ────────────────────────────────────────────────────

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "chatbot-backend"}

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── DB init on startup ───────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    try:
        from .database import create_tables
        await create_tables()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.warning(f"⚠️ Could not create DB tables (non-fatal): {e}")


# ── Checkpointer (PostgreSQL → MemorySaver fallback) ────────────────

DATABASE_URL = os.getenv("DATABASE_URL")
checkpointer = None

if DATABASE_URL:
    try:
        from psycopg_pool import ConnectionPool
        from langgraph.checkpoint.postgres import PostgresSaver

        pool = ConnectionPool(
            conninfo=DATABASE_URL,
            max_size=10,
            min_size=1,
            max_lifetime=3600,
            reconnect_timeout=30,
            check=ConnectionPool.check_connection,
        )
        checkpointer = PostgresSaver(pool)
        logger.info("✅ PostgresSaver inicializado correctamente con Cloud SQL")
    except Exception as e:
        logger.error(f"❌ Error al conectar PostgresSaver: {e}")
        checkpointer = None

if checkpointer is None:
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    if DATABASE_URL:
        logger.warning("⚠️ PostgreSQL falló. Usando MemorySaver como fallback.")
    else:
        logger.warning("⚠️ DATABASE_URL no configurado. Usando MemorySaver.")

from .agent import builder
graph_with_memory = builder.compile(checkpointer=checkpointer)


# ── Tenant registration ──────────────────────────────────────────────

from .tenants import TenantConfig, register_tenant
from .whatsapp import handle_cootradecun, handle_explouse

# Cootradecun — LangGraph multi-agent
_cootradecun_handler = functools.partial(handle_cootradecun, graph_with_memory=graph_with_memory)

register_tenant(TenantConfig(
    name="Cootradecun",
    phone_number_id=os.getenv("COOTRADECUN_PHONE_NUMBER_ID", ""),
    access_token=os.getenv("COOTRADECUN_ACCESS_TOKEN", ""),
    verify_token=os.getenv("COOTRADECUN_VERIFY_TOKEN", ""),
    handler=_cootradecun_handler,
))

# Explouse — simple direct LLM
register_tenant(TenantConfig(
    name="Xplouse",
    phone_number_id=os.getenv("EXPLOUSE_PHONE_NUMBER_ID", ""),
    access_token=os.getenv("EXPLOUSE_ACCESS_TOKEN", ""),
    verify_token=os.getenv("EXPLOUSE_VERIFY_TOKEN", ""),
    handler=handle_explouse,
))


# ── Chat endpoint (React frontend — Cootradecun only) ────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    messages: List[Dict[str, Any]]
    thread_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=request.message)], "context": {}}

    logger.info(f"📥 New message from thread {thread_id}: '{request.message[:50]}...'")

    current_state = graph_with_memory.get_state(config)
    if current_state and current_state.values:
        dialog_state = current_state.values.get("dialog_state", [])
        msg_count = len(current_state.values.get("messages", []))
        logger.info(f"📊 Current state: dialog_stack={dialog_state}, messages={msg_count}")
    else:
        logger.info("📊 No prior state for this thread (new conversation)")

    try:
        final_state = graph_with_memory.invoke(inputs, config=config)
        messages = final_state.get("messages", [])
        last_message = messages[-1] if messages else None

        if isinstance(last_message, AIMessage):
            content = last_message.content
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
            response_messages = [{"role": "assistant", "content": content or "No pude generar una respuesta."}]
        else:
            response_messages = [{"role": "assistant", "content": "Lo siento, hubo un error procesando tu solicitud."}]

        return ChatResponse(messages=response_messages, thread_id=thread_id)

    except Exception as e:
        import traceback
        logger.error(f"❌ Error in chat_endpoint: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ── WhatsApp Webhook ─────────────────────────────────────────────────

from .tenants import get_tenant, get_tenant_by_verify_token
from .whatsapp import parse_incoming_message


@app.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """
    Webhook verification (GET) — shared by all tenants.
    Meta sends hub.verify_token; we look it up in the tenant registry.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    tenant = get_tenant_by_verify_token(token)
    if mode == "subscribe" and tenant:
        logger.info(f"✅ Webhook verified for tenant: {tenant.name}")
        return PlainTextResponse(content=challenge or "", status_code=200)

    logger.warning(f"❌ Webhook verification failed — unknown token: {token!r}")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/whatsapp")
async def whatsapp_webhook_receive(request: Request, background_tasks: BackgroundTasks):
    """
    Receive incoming WhatsApp messages from any registered tenant.
    Returns 200 immediately; processing is delegated to Cloud Tasks.
    Falls back to background_tasks if Cloud Tasks is not configured (local dev).
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    parsed = parse_incoming_message(payload)

    if parsed:
        tenant = get_tenant(parsed["phone_number_id"])
        if tenant:
            is_production = os.getenv("ENVIRONMENT", "development") == "production"

            if is_production:
                # Production: delegate to Cloud Tasks (async, with retry)
                from .cloud_tasks import enqueue_message
                enqueue_message(parsed, tenant.name)
            else:
                # Local dev: process directly with background_tasks
                logger.info("⚙️ Dev mode — using background_tasks (set ENVIRONMENT=production for Cloud Tasks)")
                background_tasks.add_task(
                    tenant.handler,
                    sender_phone=parsed["sender"],
                    text=parsed["text"],
                    message_id=parsed["message_id"],
                    tenant=tenant,
                    sender_name=parsed["name"],
                )
        else:
            logger.warning(
                f"⚠️ No tenant found for phone_number_id={parsed['phone_number_id']!r} — message ignored."
            )

    return {"status": "ok"}


# ── Internal endpoint for Cloud Tasks ────────────────────────────────

class ProcessMessageRequest(BaseModel):
    sender: str
    text: str
    message_id: str
    name: str
    phone_number_id: str
    tenant_name: str


@app.post("/internal/process-message")
async def internal_process_message(
    body: ProcessMessageRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Called exclusively by Cloud Tasks to process a WhatsApp message.
    Validates the X-Internal-Secret header before processing.
    """
    from .cloud_tasks import INTERNAL_SECRET

    secret = request.headers.get("X-Internal-Secret", "")
    if not INTERNAL_SECRET or secret != INTERNAL_SECRET:
        logger.warning("❌ /internal/process-message: unauthorized request")
        raise HTTPException(status_code=403, detail="Forbidden")

    tenant = get_tenant(body.phone_number_id)
    if not tenant:
        logger.warning(f"⚠️ /internal/process-message: unknown phone_number_id={body.phone_number_id!r}")
        raise HTTPException(status_code=404, detail="Tenant not found")

    logger.info(f"⚙️ Processing task: tenant={tenant.name} from=+{body.sender}")

    background_tasks.add_task(
        tenant.handler,
        sender_phone=body.sender,
        text=body.text,
        message_id=body.message_id,
        tenant=tenant,
        sender_name=body.name,
    )

    return {"status": "accepted"}


@app.get("/whatsapp/status")
async def whatsapp_status():
    """List all registered tenants and their configuration status."""
    from .tenants import registered_tenants
    return {
        "tenants": [
            {
                "name": t.name,
                "phone_number_id_suffix": t.phone_number_id[-4:] if t.phone_number_id else None,
                "configured": bool(t.phone_number_id and t.access_token and t.verify_token),
            }
            for t in registered_tenants()
        ]
    }
