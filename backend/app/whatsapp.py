"""
WhatsApp Business Cloud API Integration Module.

Handles incoming webhook events from Meta and sends replies
via the WhatsApp Cloud API (Graph API v21.0).

This module works alongside the existing React frontend —
both channels share the same LangGraph agent and checkpointer.
"""

import os
import logging
from typing import Optional, Tuple

import httpx
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

# --- Configuration (from environment) ---
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
GRAPH_API_VERSION = "v21.0"
GRAPH_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def is_whatsapp_configured() -> bool:
    """Check if all required WhatsApp env vars are set."""
    return all([WHATSAPP_VERIFY_TOKEN, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID])


# ── Webhook verification (GET) ──────────────────────────────────────

def verify_webhook(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Tuple[bool, str]:
    """
    Verify the webhook subscription request from Meta.

    Meta sends a GET with hub.mode, hub.verify_token, and hub.challenge.
    We must return the challenge string if the token matches.

    Returns:
        (success, challenge_or_error_message)
    """
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ WhatsApp webhook verified successfully")
        return True, challenge or ""
    logger.warning("❌ WhatsApp webhook verification failed (token mismatch)")
    return False, "Verification failed"


# ── Parse incoming message ───────────────────────────────────────────

def parse_incoming_message(payload: dict) -> Optional[dict]:
    """
    Extract the first text message from a WhatsApp webhook payload.

    Returns a dict with keys: sender, text, message_id, name
    or None if the payload doesn't contain a user text message.
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

        # Only handle text messages for now
        if msg.get("type") != "text":
            logger.info(f"⏭️ Ignoring non-text message type: {msg.get('type')}")
            return None

        # Extract sender name from contacts if available
        contacts = value.get("contacts", [])
        sender_name = contacts[0].get("profile", {}).get("name", "Usuario") if contacts else "Usuario"

        return {
            "sender": msg["from"],         # phone number (e.g. "573001234567")
            "text": msg["text"]["body"],
            "message_id": msg["id"],
            "name": sender_name,
        }

    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing WhatsApp payload: {e}")
        return None


# ── Send message via Graph API ───────────────────────────────────────

async def send_text_message(to: str, text: str) -> bool:
    """
    Send a text message to a WhatsApp user via the Cloud API.

    WhatsApp has a 4096-character limit per message, so we split
    long responses into multiple messages.

    Args:
        to:   Recipient phone number (without '+')
        text: Message content

    Returns:
        True if all message parts were sent successfully
    """
    url = f"{GRAPH_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Split long messages (WhatsApp limit: 4096 chars)
    max_len = 4000  # Leave some margin
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for chunk in chunks:
            body = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": chunk},
            }

            try:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    logger.info(f"📤 WhatsApp message sent to ...{to[-4:]}")
                else:
                    logger.error(f"❌ WhatsApp send failed ({resp.status_code}): {resp.text}")
                    return False
            except httpx.HTTPError as e:
                logger.error(f"❌ HTTP error sending WhatsApp message: {e}")
                return False

    return True


# ── Mark message as read ─────────────────────────────────────────────

async def mark_as_read(message_id: str) -> None:
    """Mark an incoming message as read (shows blue ticks)."""
    url = f"{GRAPH_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
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
            pass  # Non-critical, don't fail on read receipts


# ── Process message through the chatbot ──────────────────────────────

async def save_message(
    session_id: str,
    user_phone: str,
    user_name: str,
    role: str,
    message: str,
    wa_message_id: str = None,
    department: str = None,
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
                message_type="text",
                created_at=datetime.utcnow(),
            )
            session.add(conv)
            await session.commit()
    except Exception as e:
        logger.error(f"⚠️ Failed to save message to DB: {e}")


async def process_whatsapp_message(
    sender_phone: str,
    text: str,
    message_id: str,
    graph_with_memory,
    sender_name: str = "Usuario",
) -> None:
    """
    Process an incoming WhatsApp message through the LangGraph agent
    and send the response back via WhatsApp.

    Uses the sender's phone number as the thread_id so conversation
    state persists across messages (same as React frontend uses
    thread_id for its sessions).
    """
    # Use phone number as thread_id for conversation persistence
    thread_id = f"wa-{sender_phone}"
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "messages": [HumanMessage(content=text)],
        "context": {},
    }

    logger.info(f"📥 WhatsApp message from ...{sender_phone[-4:]}: '{text[:80]}...'")

    try:
        # Mark as read immediately (shows blue ticks)
        await mark_as_read(message_id)

        # Save incoming user message to database
        await save_message(
            session_id=thread_id,
            user_phone=sender_phone,
            user_name=sender_name,
            role="user",
            message=text,
            wa_message_id=message_id,
        )

        # Invoke the same graph used by the React frontend
        final_state = graph_with_memory.invoke(inputs, config=config)

        # Extract the AI response
        messages = final_state.get("messages", [])
        last_message = messages[-1] if messages else None

        if isinstance(last_message, AIMessage) and last_message.content:
            content = last_message.content
            # Handle Gemini's list-style content
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""

            response_text = content or "Lo siento, no pude generar una respuesta."
        else:
            response_text = "Lo siento, hubo un error procesando tu solicitud."

        # Send response back via WhatsApp
        success = await send_text_message(sender_phone, response_text)

        # Save assistant response to database
        await save_message(
            session_id=thread_id,
            user_phone=sender_phone,
            user_name=sender_name,
            role="assistant",
            message=response_text,
        )

        if success:
            logger.info(f"✅ WhatsApp reply sent to ...{sender_phone[-4:]} ({len(response_text)} chars)")
        else:
            logger.error(f"❌ Failed to send WhatsApp reply to ...{sender_phone[-4:]}")

    except Exception as e:
        logger.error(f"❌ Error processing WhatsApp message: {e}")
        # Try to send an error message back to the user
        try:
            await send_text_message(
                sender_phone,
                "Lo siento, ocurrió un error. Por favor intenta de nuevo en un momento. 🙏"
            )
        except Exception:
            pass

