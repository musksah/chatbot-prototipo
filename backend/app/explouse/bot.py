"""
Xplouse WhatsApp Bot — Simple direct LLM handler.

Unlike Cootradecun (which uses a LangGraph multi-agent system),
Xplouse uses a straightforward single-LLM approach:
  user message → Gemini with system prompt → response

Conversation history is kept in memory per thread_id using a simple
list stored in a dict. For production, replace with a DB-backed store.
"""

import os
import logging
from collections import defaultdict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — edit this to define Xplouse's personality and purpose
# ---------------------------------------------------------------------------
EXPLOUSE_SYSTEM_PROMPT = """\
Eres el asistente virtual de Xplouse, una empresa de tecnología especializada \
en soluciones de inteligencia artificial y automatización para negocios.

Ayudas a los usuarios con:
- Información sobre los productos y servicios de Xplouse
- Soporte técnico básico
- Orientación sobre cómo contratar o probar los servicios

Responde siempre en español, de forma amable, concisa y profesional.
Si no tienes información suficiente para responder algo, indícalo honestamente \
y ofrece conectar al usuario con un asesor humano.
"""

# ---------------------------------------------------------------------------
# In-memory conversation history (thread_id → list of messages)
# For production: replace with PostgreSQL or Redis
# ---------------------------------------------------------------------------
_histories: dict[str, list] = defaultdict(list)
MAX_HISTORY = 20  # keep last N messages to avoid token bloat


# Module-level singleton — avoid re-initializing the HTTP client on every message
_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
)


async def get_response(text: str, thread_id: str) -> str:
    """
    Process a user message and return the bot's response.

    Args:
        text:      The user's message.
        thread_id: Unique conversation ID (e.g. "wa-573001234567").

    Returns:
        The assistant's response as a plain string.
    """
    history = _histories[thread_id]

    # Append the new user message
    history.append(HumanMessage(content=text))

    # Trim history to avoid token bloat
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    messages = [SystemMessage(content=EXPLOUSE_SYSTEM_PROMPT)] + history

    try:
        result = await _llm.ainvoke(messages)
        response_text = result.content or "Lo siento, no pude generar una respuesta."

        # Save assistant response to history
        history.append(AIMessage(content=response_text))
        return response_text

    except Exception as e:
        logger.error(f"❌ Xplouse LLM error for thread {thread_id}: {e}")
        return "Lo siento, ocurrió un error. Por favor intenta de nuevo en un momento."
