"""
WhatsApp Business Cloud API Integration Module.

Handles incoming webhook events from Meta and sends replies
via the WhatsApp Cloud API (Graph API v22.0).

Supports multiple tenants (WABAs): credentials (access_token,
phone_number_id) are passed per-call instead of read from globals,
allowing different bots to share this module.
"""

import logging
from typing import Optional

import httpx
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)

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


# ── Save message to DB ───────────────────────────────────────────────

async def save_message(
    session_id: str,
    user_phone: str,
    user_name: str,
    role: str,
    message: str,
    wa_message_id: str = None,
    department: str = None,
    tenant: str = None,
) -> None:
    """Save a message to the conversations table."""
    try:
        import uuid
        from .database import _ensure_engine, async_session_factory
        from .models.chatbot import Conversation
        from datetime import datetime

        _ensure_engine()
        if async_session_factory is None:
            logger.warning("⚠️ Database not configured, skipping message save")
            return

        async with async_session_factory() as session:
            conv = Conversation(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_phone=user_phone,
                user_name=user_name,
                role=role,
                message=message,
                wa_message_id=wa_message_id,
                department=department,
                tenant=tenant,
                message_type="text",
                created_at=datetime.utcnow(),
            )
            session.add(conv)
            await session.commit()
    except Exception as e:
        logger.error(f"⚠️ Failed to save message to DB: {e}")


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
    """
    thread_id = f"wa-{sender_phone}"
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=text)], "context": {}}

    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"📨 Nuevo mensaje → Cootradecun")
    logger.info(f"   De:      +{sender_phone} ({sender_name})")
    logger.info(f"   Mensaje: {text[:120]}")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        await mark_as_read(message_id, tenant.phone_number_id, tenant.access_token)
        await save_message(
            session_id=thread_id,
            user_phone=sender_phone,
            user_name=sender_name,
            role="user",
            message=text,
            wa_message_id=message_id,
            tenant=tenant.name,
        )

        final_state = graph_with_memory.invoke(inputs, config=config)
        messages = final_state.get("messages", [])
        last_message = messages[-1] if messages else None

        if isinstance(last_message, AIMessage) and last_message.content:
            content = last_message.content
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
            response_text = content or "Lo siento, no pude generar una respuesta."
        else:
            response_text = "Lo siento, hubo un error procesando tu solicitud."

        success = await send_text_message(
            sender_phone, response_text,
            tenant.phone_number_id, tenant.access_token,
        )
        await save_message(
            session_id=thread_id,
            user_phone=sender_phone,
            user_name=sender_name,
            role="assistant",
            message=response_text,
            tenant=tenant.name,
        )
        if success:
            logger.info(f"✅ [Cootradecun] Reply sent to ...{sender_phone[-4:]}")

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
    """
    from .explouse.bot import get_response

    thread_id = f"wa-{sender_phone}"

    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"📨 Nuevo mensaje → Xplouse")
    logger.info(f"   De:      +{sender_phone} ({sender_name})")
    logger.info(f"   Mensaje: {text[:120]}")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        await mark_as_read(message_id, tenant.phone_number_id, tenant.access_token)
        await save_message(
            session_id=thread_id,
            user_phone=sender_phone,
            user_name=sender_name,
            role="user",
            message=text,
            wa_message_id=message_id,
            tenant=tenant.name,
        )

        response_text = await get_response(text, thread_id=thread_id)

        success = await send_text_message(
            sender_phone, response_text,
            tenant.phone_number_id, tenant.access_token,
        )
        await save_message(
            session_id=thread_id,
            user_phone=sender_phone,
            user_name=sender_name,
            role="assistant",
            message=response_text,
            tenant=tenant.name,
        )
        if success:
            logger.info(f"✅ [Explouse] Reply sent to ...{sender_phone[-4:]}")

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
