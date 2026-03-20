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


# ── Chat result storage (PostgreSQL) ─────────────────────────────────

async def _store_chat_result(task_id: str, thread_id: str, status: str, messages: list = None) -> None:
    from .database import _ensure_engine, async_session_factory
    from sqlalchemy import text
    _ensure_engine()
    if async_session_factory is None:
        return
    async with async_session_factory() as session:
        await session.execute(text("""
            INSERT INTO chat_results (task_id, thread_id, status, messages, created_at)
            VALUES (:task_id, :thread_id, :status, :messages, NOW())
            ON CONFLICT (task_id) DO UPDATE
              SET status = EXCLUDED.status, messages = EXCLUDED.messages
        """), {
            "task_id": task_id,
            "thread_id": thread_id,
            "status": status,
            "messages": __import__("json").dumps(messages) if messages else None,
        })
        await session.commit()


async def _get_chat_result(task_id: str) -> Optional[Dict]:
    from .database import _ensure_engine, async_session_factory
    from sqlalchemy import text
    _ensure_engine()
    if async_session_factory is None:
        return None
    async with async_session_factory() as session:
        row = (await session.execute(
            text("SELECT task_id, thread_id, status, messages FROM chat_results WHERE task_id = :tid"),
            {"tid": task_id}
        )).fetchone()
        if not row:
            return None
        return {"task_id": row[0], "thread_id": row[1], "status": row[2], "messages": __import__("json").loads(row[3]) if row[3] else None}


# ── Chat endpoint (React frontend — Cootradecun only) ────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    messages: Optional[List[Dict[str, Any]]] = None
    thread_id: str
    task_id: Optional[str] = None
    status: Optional[str] = None  # "pending" | "completed" | "failed"


def _run_graph(thread_id: str, message: str) -> List[Dict[str, Any]]:
    """Run LangGraph synchronously and return response messages."""
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=message)], "context": {}}

    current_state = graph_with_memory.get_state(config)
    if current_state and current_state.values:
        dialog_state = current_state.values.get("dialog_state", [])
        msg_count = len(current_state.values.get("messages", []))
        logger.info(f"📊 Current state: dialog_stack={dialog_state}, messages={msg_count}")
    else:
        logger.info("📊 No prior state for this thread (new conversation)")

    final_state = graph_with_memory.invoke(inputs, config=config)
    messages = final_state.get("messages", [])
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage):
        content = last_message.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        return [{"role": "assistant", "content": content or "No pude generar una respuesta."}]
    return [{"role": "assistant", "content": "Lo siento, hubo un error procesando tu solicitud."}]


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    logger.info(f"📥 New message from thread {thread_id}: '{request.message[:50]}...'")

    if is_production:
        # Async path: enqueue Cloud Task, return task_id for polling
        from .cloud_tasks import enqueue_chat
        task_id = str(uuid.uuid4())
        await _store_chat_result(task_id, thread_id, "pending")
        enqueue_chat(task_id, request.message, thread_id)
        return ChatResponse(task_id=task_id, thread_id=thread_id, status="pending")

    # Dev path: process synchronously
    try:
        response_messages = _run_graph(thread_id, request.message)
        return ChatResponse(messages=response_messages, thread_id=thread_id, status="completed")
    except Exception as e:
        import traceback
        logger.error(f"❌ Error in chat_endpoint: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/fake_whatsapp", response_model=ChatResponse)
async def chat_endpoint_fake_whatsapp(request: ChatRequest):
    """
    Simulates a WhatsApp conversation and writes all metadata to the v3.0 DB schema.

    Fills: whatsapp_contacts, sessions, interaction_log.
    Counters written per turn: total_messages, user_messages, bot_messages,
    fallback_count, primary_intent, tokens, estimated_cost_usd.
    """
    import time as _time
    from .db_writer import (
        upsert_contact,
        upsert_session,
        log_interaction,
        update_session_stats,
        increment_contact_messages,
    )

    phone = request.phone or "573000000001"
    name  = request.name  or "Usuario Test"

    thread_id = request.thread_id or str(uuid.uuid4())
    config    = {"configurable": {"thread_id": thread_id}}
    inputs    = {"messages": [HumanMessage(content=request.message)], "context": {}}

    logger.info(f"📥 [fake_wa] thread={thread_id} phone={phone} msg='{request.message[:50]}'")

    # ── 1. Ensure contact exists ──────────────────────────────────────────────
    contact_id = await upsert_contact(phone, name)

    # ── 2. Get or create session (24 h window) ────────────────────────────────
    session_id = None
    if contact_id:
        session_key = f"fake-{phone}"
        session_id  = await upsert_session(contact_id, session_key)

    # ── 3. Log the USER turn ──────────────────────────────────────────────────
    if session_id:
        await log_interaction(
            session_id,
            "user",
            detected_intent=None,   # intent is detected after bot responds
            tokens_in=0,
            tokens_out=0,
        )

    # ── 4. Invoke agent (measure latency) ────────────────────────────────────
    t0 = _time.perf_counter()
    try:
        final_state = graph_with_memory.invoke(inputs, config=config)
    except Exception as e:
        import traceback
        logger.error(f"❌ [fake_wa] agent error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    response_ms = int((_time.perf_counter() - t0) * 1000)

    # ── 5. Extract bot response ───────────────────────────────────────────────
    messages_out = final_state.get("messages", [])
    last_message = messages_out[-1] if messages_out else None

    if isinstance(last_message, AIMessage):
        content = last_message.content
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        bot_text = content or "No pude generar una respuesta."
    else:
        bot_text = "Lo siento, hubo un error procesando tu solicitud."

    response_messages = [{"role": "assistant", "content": bot_text}]

    # ── 6. Classify the turn ─────────────────────────────────────────────────
    is_fallback     = _detect_fallback(bot_text)
    dialog_state    = final_state.get("dialog_state", [])
    detected_intent = _extract_intent(dialog_state)

    # Token usage from the in‑memory accumulator keyed by thread_id
    from .agent import _token_totals_by_thread
    token_totals    = _token_totals_by_thread.get(thread_id, {})
    tokens_in_turn  = token_totals.get("prompt_tokens", 0)
    tokens_out_turn = token_totals.get("completion_tokens", 0)
    cost_delta      = tokens_out_turn * _COST_PER_OUTPUT_TOKEN_USD

    # ── 7. Log the ASSISTANT turn ─────────────────────────────────────────────
    if session_id:
        await log_interaction(
            session_id,
            "assistant",
            detected_intent=detected_intent,
            tokens_in=tokens_in_turn,
            tokens_out=tokens_out_turn,
            response_ms=response_ms,
            is_fallback=is_fallback,
            fallback_message=request.message if is_fallback else None,
        )

        # ── 8. Update session counters ────────────────────────────────────────
        await update_session_stats(
            session_id,
            user_messages_delta=1,
            bot_messages_delta=1,
            fallback_delta=1 if is_fallback else 0,
            primary_intent=detected_intent,
            tokens_input_delta=tokens_in_turn,
            tokens_output_delta=tokens_out_turn,
            estimated_cost_delta=cost_delta,
        )

    # ── 9. Update contact message counter ────────────────────────────────────
    if contact_id:
        # 2 messages per turn: 1 user + 1 bot
        await increment_contact_messages(phone, count=2)

    logger.info(
        f"✅ [fake_wa] thread={thread_id} session={session_id} "
        f"intent={detected_intent} fallback={is_fallback} "
        f"tokens_in={tokens_in_turn} tokens_out={tokens_out_turn} "
        f"response_ms={response_ms}ms"
    )

    return ChatResponse(messages=response_messages, thread_id=thread_id)



@app.get("/chat/result/{task_id}", response_model=ChatResponse)
async def chat_result(task_id: str):
    """Poll for the result of an async chat task."""
    result = await _get_chat_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return ChatResponse(
        task_id=result["task_id"],
        thread_id=result["thread_id"],
        status=result["status"],
        messages=result["messages"],
    )


# ── Internal endpoint for Cloud Tasks (chat) ─────────────────────────

class ProcessChatRequest(BaseModel):
    task_id: str
    message: str
    thread_id: str


@app.post("/internal/process-chat")
async def internal_process_chat(body: ProcessChatRequest, request: Request):
    """Called by Cloud Tasks to process a /chat request asynchronously."""
    from .cloud_tasks import INTERNAL_SECRET
    secret = request.headers.get("X-Internal-Secret", "")
    if not INTERNAL_SECRET or secret != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"⚙️ Processing chat task: task_id={body.task_id} thread_id={body.thread_id}")
    try:
        response_messages = _run_graph(body.thread_id, body.message)
        await _store_chat_result(body.task_id, body.thread_id, "completed", response_messages)
        logger.info(f"✅ Chat task completed: task_id={body.task_id}")
    except Exception as e:
        logger.error(f"❌ Chat task failed: task_id={body.task_id} error={e}")
        await _store_chat_result(body.task_id, body.thread_id, "failed",
                                  [{"role": "assistant", "content": "Lo siento, ocurrió un error. Por favor intenta de nuevo."}])
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}


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
