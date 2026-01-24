import uuid
from dotenv import load_dotenv
load_dotenv() # Load env vars from .env file

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from .agent import graph

app = FastAPI(title="Cootradecun Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Cloud Run
@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "chatbot-backend"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/debug-gcs")
async def debug_gcs():
    import google.auth
    from google.auth.transport import requests as auth_requests
    from .gcs_storage import upload_and_get_signed_url
    from . import gcs_storage
    from io import BytesIO
    import traceback
    import os
    import inspect
    
    debug_info = {}
    
    try:
        # Check credentials
        credentials, project = google.auth.default()
        if not hasattr(credentials, 'service_account_email') or not credentials.service_account_email:
            auth_request = auth_requests.Request()
            credentials.refresh(auth_request)
            
        debug_info["service_account_from_auth"] = getattr(credentials, "service_account_email", "Not found")
        debug_info["project"] = project
        
        # Check Env Var
        debug_info["env_service_account_email"] = os.getenv("SERVICE_ACCOUNT_EMAIL", "MISSING_OR_EMPTY")
        
        # Check Source Code to verify deployment update
        try:
            source = inspect.getsource(gcs_storage.generate_signed_url)
            debug_info["source_snippet"] = source[:1000] # Enough to see the fallback logic
        except Exception as source_e:
             debug_info["source_error"] = str(source_e)
        
        # Try upload
        dummy_pdf = BytesIO(b"PDF de prueba para debugging")
        success, result = upload_and_get_signed_url(dummy_pdf, "debug_test", expiration_hours=1)
        
        return {
            "success": success,
            "result": result,
            "debug_info": debug_info
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "debug_info": debug_info
        }

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    messages: List[Dict[str, Any]]
    thread_id: str

# --- Checkpointer Configuration ---
# PostgresSaver for production (multi-instance Cloud Run)
# MemorySaver as fallback for local dev without database


import os
import logging

# Configure checkpointer based on DATABASE_URL availability
DATABASE_URL = os.getenv("DATABASE_URL")
logger = logging.getLogger(__name__)

checkpointer = None

if DATABASE_URL:
    # Use PostgreSQL for multi-instance persistence (Cloud Run)
    # NOTE: Tables must be created manually - see backend/docs/checkpoint_tables.sql
    try:
        from psycopg_pool import ConnectionPool
        from langgraph.checkpoint.postgres import PostgresSaver
        
        # Create a connection pool with reconnection handling
        # - max_lifetime: close connections after 1 hour to avoid stale connections
        # - reconnect_timeout: time to wait for reconnection
        # - check: validate connections before borrowing from pool
        pool = ConnectionPool(
            conninfo=DATABASE_URL,
            max_size=10,
            min_size=1,
            max_lifetime=3600,  # 1 hour - prevents stale connections after inactivity
            reconnect_timeout=30,
            check=ConnectionPool.check_connection,  # Validate connection is alive
        )
        
        # Create PostgresSaver with the pool (tables must exist)
        checkpointer = PostgresSaver(pool)
        
        logger.info("✅ PostgresSaver inicializado correctamente con Cloud SQL")
    except Exception as e:
        logger.error(f"❌ Error al conectar PostgresSaver: {e}")
        logger.warning("⚠️ Fallback a MemorySaver (no persistente)")
        checkpointer = None

if checkpointer is None:
    # Fallback to in-memory for local dev without database
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    if DATABASE_URL:
        logger.warning("⚠️ PostgreSQL falló. Usando MemorySaver como fallback.")
    else:
        logger.warning("⚠️ DATABASE_URL no configurado. Usando MemorySaver (no persistente entre instancias).")

# Re-compile graph with checkpointer
from .agent import builder
graph_with_memory = builder.compile(checkpointer=checkpointer)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    
    inputs = {
        "messages": [HumanMessage(content=request.message)]
    }
    
    # Log incoming request
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"📥 New message from thread {thread_id}: '{request.message[:50]}...'")
    
    # Check current state before invocation
    current_state = graph_with_memory.get_state(config)
    if current_state and current_state.values:
        dialog_state = current_state.values.get("dialog_state", [])
        msg_count = len(current_state.values.get("messages", []))
        logger.info(f"📊 Current state: dialog_stack={dialog_state}, messages={msg_count}")
    else:
        logger.info(f"📊 No prior state for this thread (new conversation)")
    
    # We want to stream the output or get the final state.
    # invoke() returns the final state.
    try:
        final_state = graph_with_memory.invoke(inputs, config=config)
        
        # Log the final state for debugging
        logger.info(f"📤 Final state keys: {final_state.keys()}")
        
        # Extract the last message if it's an AI message
        messages = final_state.get("messages", [])
        logger.info(f"📤 Total messages in state: {len(messages)}")
        
        last_message = messages[-1] if messages else None
        
        if last_message:
            logger.info(f"📤 Last message type: {type(last_message).__name__}")
            logger.info(f"📤 Last message content: {str(last_message.content)[:100] if last_message.content else 'None/Empty'}")
        
        response_messages = []
        if isinstance(last_message, AIMessage):
            content = last_message.content
            # Handle case where content might be a list (Gemini format)
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
            response_messages.append({"role": "assistant", "content": content or "No pude generar una respuesta."})
        else:
            # If the last message wasn't AI (unlikely unless error), send something generic
            response_messages.append({"role": "assistant", "content": "Lo siento, hubo un error procesando tu solicitud."})

        return ChatResponse(
            messages=response_messages,
            thread_id=thread_id
        )

    except Exception as e:
        import traceback
        logger.error(f"❌ Error in chat_endpoint: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
