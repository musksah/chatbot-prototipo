"""
WhatsApp Business Cloud API Integration Module.

Handles incoming webhook events from Meta and sends replies
via the WhatsApp Cloud API (Graph API v22.0).

Supports multiple tenants (WABAs): credentials (access_token,
phone_number_id) are passed per-call instead of read from globals,
allowing different bots to share this module.
"""

import logging
import time
from typing import Optional

import httpx
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)


# ── Fallback detection ───────────────────────────────────────────────

_FALLBACK_PHRASES = (
    "lo siento, ocurrió un error",
    "no pude generar una respuesta",
    "hubo un error procesando",
    "lo siento, ocurrió un error. por favor intenta de nuevo",
)


def _is_fallback(text) -> bool:
    """Detecta si la respuesta del bot es un mensaje de error/fallback."""
    # Gemini can return a list in AFC mode — safely extract text first
    if isinstance(text, list):
        text = text[0].get("text", "") if text else ""
    lowered = str(text).lower()
    return any(phrase in lowered for phrase in _FALLBACK_PHRASES)

GRAPH_API_VERSION = "v22.0"
GRAPH_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


# ── Parse incoming message ───────────────────────────────────────────

def parse_incoming_message(payload: dict) -> Optional[dict]:
    """
    Extract the first text message from a WhatsApp webhook payload.

    Returns a dict with keys: sender, text, message_id, name, phone_number_id
    or None if the payload doesn't contain a user text message.

    phone_number_id identifies which WABA/tenant the message belongs to.
    """
    try:
        entry = payload.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]

        if msg.get("type") != "text":
            logger.info(f"⏭️ Ignoring non-text message type: {msg.get('type')}")
            return None

        # Identify the receiving WABA phone number
        metadata = value.get("metadata", {})
        phone_number_id = metadata.get("phone_number_id")

        contacts = value.get("contacts", [])
        sender_name = contacts[0].get("profile", {}).get("name", "Usuario") if contacts else "Usuario"

        return {
            "sender": msg["from"],
            "text": msg["text"]["body"],
            "message_id": msg["id"],
            "name": sender_name,
            "phone_number_id": phone_number_id,  # used for tenant routing
        }

    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing WhatsApp payload: {e}")
        return None


# ── Send message via Graph API ───────────────────────────────────────

async def send_text_message(
    to: str,
    text: str,
    phone_number_id: str,
    access_token: str,
) -> bool:
    """
    Send a text message to a WhatsApp user via the Cloud API.

    WhatsApp has a 4096-character limit per message, so long responses
    are split into multiple messages.

    Args:
        to:               Recipient phone number (without '+')
        text:             Message content
        phone_number_id:  The sending WABA phone number ID
        access_token:     The WABA access token
    """
    url = f"{GRAPH_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    max_len = 4000
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]

    total_chunks = len(chunks)
    logger.info(f"📤 Sending message to +{to} ({total_chunks} chunk(s), {len(text)} chars)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, chunk in enumerate(chunks, 1):
            body = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"preview_url": False, "body": chunk},
            }
            try:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    logger.info(f"✅ Chunk {i}/{total_chunks} delivered to +{to}")
                else:
                    logger.error(f"❌ WhatsApp send failed ({resp.status_code}) to +{to}: {resp.text}")
                    return False
            except httpx.HTTPError as e:
                logger.error(f"❌ HTTP error sending to +{to}: {e}")
                return False

    return True


# ── Mark message as read ─────────────────────────────────────────────

async def mark_as_read(
    message_id: str,
    phone_number_id: str,
    access_token: str,
) -> None:
    """Mark an incoming message as read (shows blue ticks)."""
    url = f"{GRAPH_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, headers=headers, json=body)
        except httpx.HTTPError:
            pass


# ── Tenant handlers ───────────────────────────────────────────────────
# These are imported and registered in main.py so they can reference
# the compiled graph (Cootradecun) or the simple LLM (Explouse).

async def handle_cootradecun(
    sender_phone: str,
    text: str,
    message_id: str,
    tenant,  # TenantConfig
    sender_name: str = "Usuario",
    graph_with_memory=None,
) -> None:
    """
    Process a Cootradecun message through the LangGraph multi-agent system.
    graph_with_memory is injected via functools.partial in main.py.

    Single-write to the unified `conversations` table (v4.0 schema).
    Also updates contacts and session stats.

    Sessions span 24 hours — close_session is NOT called here anymore.
    The session stays active until upsert_session detects a 24h gap on the next message.
    """
    from .db_writer import (
        upsert_contact, upsert_session, save_conversation,
        update_session_stats, increment_contact_messages,
    )

    _COST_PER_OUTPUT_TOKEN = 0.0000025  # Gemini Flash pricing

    thread_id = f"wa-{sender_phone}"
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=text)]}

    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"📨 Nuevo mensaje → Cootradecun")
    logger.info(f"   De:      +{sender_phone} ({sender_name})")
    logger.info(f"   Mensaje: {text[:120]}")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # ── v4.0: register contact and session BEFORE processing ─────────
    contact_id = await upsert_contact(sender_phone, sender_name)
    session_id_v4 = await upsert_session(contact_id, thread_id) if contact_id else None

    try:
        await mark_as_read(message_id, tenant.phone_number_id, tenant.access_token)

        # ── Save user message ────────────────────────────────────────
        if session_id_v4:
            await save_conversation(
                session_id=session_id_v4,
                role="user",
                message=text,
                user_phone=sender_phone,
                user_name=sender_name,
                wa_message_id=message_id,
                tenant=tenant.name,
            )

        # ── Invoke the agent and measure latency ─────────────────────
        t_start = time.monotonic()
        final_state = graph_with_memory.invoke(inputs, config=config)
        elapsed_ms = int((time.monotonic() - t_start) * 1000)

        messages = final_state.get("messages", [])
        last_message = messages[-1] if messages else None

        if isinstance(last_message, AIMessage) and last_message.content:
            content = last_message.content
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
            response_text = content or "Lo siento, no pude generar una respuesta."
        else:
            response_text = "Lo siento, hubo un error procesando tu solicitud."

        # ── Extract token usage from the last AI message ─────────────
        tokens_in = tokens_out = None
        if isinstance(last_message, AIMessage):
            from .agent import _extract_token_usage
            usage = _extract_token_usage(last_message)
            tokens_in = usage.get("prompt_tokens")
            tokens_out = usage.get("completion_tokens")
            if tokens_in or tokens_out:
                logger.info(
                    f"🔢 [Cootradecun] tokens: input={tokens_in}, output={tokens_out}"
                )

        bot_is_fallback = _is_fallback(response_text)

        success = await send_text_message(
            sender_phone, response_text,
            tenant.phone_number_id, tenant.access_token,
        )

        # ── Extract intent from dialog_state ─────────────────────────
        dialog_state = final_state.get("dialog_state", [])
        detected_intent = dialog_state[-1] if dialog_state else None

        # ── Save bot response ────────────────────────────────────────
        if session_id_v4:
            await save_conversation(
                session_id=session_id_v4,
                role="assistant",
                message=response_text,
                user_phone=sender_phone,
                user_name=sender_name,
                tenant=tenant.name,
                detected_intent=detected_intent,
                is_fallback=bot_is_fallback,
                response_time_ms=elapsed_ms,
                tokens_in=tokens_in or 0,
                tokens_out=tokens_out or 0,
            )

            # ── Update session counters ───────────────────────────────
            await update_session_stats(
                session_id_v4,
                user_messages_delta=1,
                bot_messages_delta=1,
                fallback_delta=1 if bot_is_fallback else 0,
                primary_intent=detected_intent,
                tokens_input_delta=tokens_in or 0,
                tokens_output_delta=tokens_out or 0,
                estimated_cost_delta=(tokens_out or 0) * _COST_PER_OUTPUT_TOKEN,
            )

        # ── Update contact message counter ────────────────────────────
        await increment_contact_messages(sender_phone, count=2)

        if success:
            logger.info(f"✅ [Cootradecun] Reply sent to ...{sender_phone[-4:]} ({elapsed_ms}ms)")

    except Exception as e:
        logger.error(f"❌ [Cootradecun] Error: {e}")
        try:
            await send_text_message(
                sender_phone,
                "Lo siento, ocurrió un error. Por favor intenta de nuevo. 🙏",
                tenant.phone_number_id, tenant.access_token,
            )
        except Exception:
            pass


async def handle_explouse(
    sender_phone: str,
    text: str,
    message_id: str,
    tenant,  # TenantConfig
    sender_name: str = "Usuario",
) -> None:
    """
    Process an Explouse message through the simple direct LLM bot.

    Single-write to the unified `conversations` table (v4.0 schema).

    Sessions span 24 hours — close_session is NOT called here anymore.
    The session stays active until upsert_session detects a 24h gap on the next message.
    """
    from .explouse.bot import get_response
    from .db_writer import (
        upsert_contact, upsert_session, save_conversation,
        update_session_stats, increment_contact_messages,
    )

    thread_id = f"wa-{sender_phone}"

    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"📨 Nuevo mensaje → Xplouse")
    logger.info(f"   De:      +{sender_phone} ({sender_name})")
    logger.info(f"   Mensaje: {text[:120]}")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # ── v4.0: register contact and session BEFORE processing ─────────
    contact_id = await upsert_contact(sender_phone, sender_name)
    session_id_v4 = await upsert_session(contact_id, thread_id) if contact_id else None

    try:
        await mark_as_read(message_id, tenant.phone_number_id, tenant.access_token)

        # ── Save user message ────────────────────────────────────────
        if session_id_v4:
            await save_conversation(
                session_id=session_id_v4,
                role="user",
                message=text,
                user_phone=sender_phone,
                user_name=sender_name,
                wa_message_id=message_id,
                tenant=tenant.name,
            )

        # ── Invoke the bot and measure latency ───────────────────────
        t_start = time.monotonic()
        response_text = await get_response(text, thread_id=thread_id)
        elapsed_ms = int((time.monotonic() - t_start) * 1000)

        bot_is_fallback = _is_fallback(response_text)

        success = await send_text_message(
            sender_phone, response_text,
            tenant.phone_number_id, tenant.access_token,
        )

        # ── Save bot response ────────────────────────────────────────
        if session_id_v4:
            await save_conversation(
                session_id=session_id_v4,
                role="assistant",
                message=response_text,
                user_phone=sender_phone,
                user_name=sender_name,
                tenant=tenant.name,
                is_fallback=bot_is_fallback,
                response_time_ms=elapsed_ms,
            )

            # ── Update session counters ───────────────────────────────
            await update_session_stats(
                session_id_v4,
                user_messages_delta=1,
                bot_messages_delta=1,
                fallback_delta=1 if bot_is_fallback else 0,
            )

        # ── Update contact message counter ────────────────────────────
        await increment_contact_messages(sender_phone, count=2)

        if success:
            logger.info(f"✅ [Explouse] Reply sent to ...{sender_phone[-4:]} ({elapsed_ms}ms)")

    except Exception as e:
        logger.error(f"❌ [Explouse] Error: {e}")
        try:
            await send_text_message(
                sender_phone,
                "Lo siento, ocurrió un error. Por favor intenta de nuevo. 🙏",
                tenant.phone_number_id, tenant.access_token,
            )
        except Exception:
            pass
