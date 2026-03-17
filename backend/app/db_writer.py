"""
db_writer.py — Schema v3.0 Write Layer

Encapsulates all direct writes to the v3.0 schema tables:
  - whatsapp_contacts
  - sessions
  - interaction_log

Uses asyncpg directly (bypassing SQLAlchemy) to maintain independence
from the main engine and minimize the risk of interference with the
chatbot flow.

Error handling: each function has its own try/except that logs the error
without propagating it — never blocks the chatbot flow.

Session window:
  A session spans 24 hours from the first message. If the user writes again
  within that window, the same session is reused. After 24h, the old session
  is marked 'abandoned' and a new one is created.
  Sessions that expire without a follow-up are handled by the v_sessions view,
  which computes effective_status at query time without any background job.
"""

import os
import uuid
import logging

import asyncpg

logger = logging.getLogger(__name__)

# Normalize DATABASE_URL: raw asyncpg does not accept the "+asyncpg" prefix from SQLAlchemy
_DATABASE_URL = (
    os.getenv("DATABASE_URL", "")
    .replace("postgresql+asyncpg://", "postgresql://", 1)
    .replace("postgres+asyncpg://", "postgresql://", 1)
)


# ─── Connection ─────────────────────────────────────────────────────────────

async def _get_conn() -> asyncpg.Connection | None:
    """Returns a direct asyncpg connection, or None if DATABASE_URL is not configured."""
    if not _DATABASE_URL:
        logger.warning("[db_writer] DATABASE_URL not configured — v3.0 writes disabled")
        return None
    try:
        return await asyncpg.connect(_DATABASE_URL)
    except Exception as e:
        logger.error(f"[db_writer] Could not connect to the database: {e}")
        return None


# ─── whatsapp_contacts ──────────────────────────────────────────────────────

async def upsert_contact(phone: str, name: str | None = None) -> str | None:
    """
    Creates or updates a contact in whatsapp_contacts.

    - New contact: inserts the record.
    - Existing contact: updates name, last_seen_at, increments total_sessions
      and sets is_returning to True if the contact had at least 1 prior session.

    Returns the contact UUID (str), or None on failure.
    """
    conn = await _get_conn()
    if not conn:
        return None
    try:
        row = await conn.fetchrow("""
            INSERT INTO whatsapp_contacts (phone, name, first_seen_at, last_seen_at, total_sessions, is_returning)
            VALUES ($1, $2, NOW(), NOW(), 1, FALSE)
            ON CONFLICT (phone) DO UPDATE
                SET name           = COALESCE($2, whatsapp_contacts.name),
                    last_seen_at   = NOW(),
                    total_sessions = whatsapp_contacts.total_sessions + 1,
                    is_returning   = (whatsapp_contacts.total_sessions >= 1),
                    updated_at     = NOW()
            RETURNING id::TEXT
        """, phone, name)
        contact_id = row["id"] if row else None
        if contact_id:
            logger.debug(f"[db_writer] upsert_contact OK — phone={phone} id={contact_id}")
        return contact_id
    except Exception as e:
        logger.error(f"[db_writer] upsert_contact failed (phone={phone}): {e}")
        return None
    finally:
        await conn.close()


# ─── sessions ───────────────────────────────────────────────────────────────

async def upsert_session(contact_id: str, session_key: str) -> str | None:
    """
    Returns the active session ID for the given contact within the last 24 hours.

    - If an active session exists started less than 24h ago → return its ID (conversation continues).
    - Otherwise → mark the previous active session as 'abandoned' and create a new one.

    The session_key (e.g. 'wa-573001234567') is used as a human-readable prefix;
    new sessions get a unique suffix to satisfy the UNIQUE constraint.

    Returns the session UUID (str), or None on failure.
    """
    conn = await _get_conn()
    if not conn:
        return None
    try:
        contact_uuid = uuid.UUID(contact_id)

        # 1. Look for an active session within the last 24 hours
        existing = await conn.fetchrow("""
            SELECT id::TEXT
            FROM sessions
            WHERE contact_id = $1
              AND status = 'active'
              AND started_at > NOW() - INTERVAL '24 hours'
            ORDER BY started_at DESC
            LIMIT 1
        """, contact_uuid)

        if existing:
            session_id = existing["id"]
            logger.debug(f"[db_writer] upsert_session reuse — contact={contact_id} session={session_id}")
            return session_id

        # 2. Mark any lingering active session as abandoned
        await conn.execute("""
            UPDATE sessions
            SET status           = 'abandoned',
                ended_at         = NOW(),
                duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER,
                updated_at       = NOW()
            WHERE contact_id = $1
              AND status = 'active'
        """, contact_uuid)

        # 3. Create a new session with a unique key (prefix + short UUID suffix)
        unique_key = f"{session_key}-{uuid.uuid4().hex[:8]}"
        row = await conn.fetchrow("""
            INSERT INTO sessions (session_key, contact_id, status, started_at)
            VALUES ($1, $2, 'active', NOW())
            RETURNING id::TEXT
        """, unique_key, contact_uuid)

        session_id = row["id"] if row else None
        if session_id:
            logger.debug(f"[db_writer] upsert_session new — contact={contact_id} session={session_id} key={unique_key}")
        return session_id

    except Exception as e:
        logger.error(f"[db_writer] upsert_session failed (contact={contact_id}): {e}")
        return None
    finally:
        await conn.close()


# ─── interaction_log ────────────────────────────────────────────────────────

async def log_interaction(
    session_id: str,
    role: str,
    *,
    detected_intent: str | None = None,
    intent_confidence: float | None = None,   # reserved for future use
    tokens_in: int = 0,
    tokens_out: int = 0,
    response_ms: int | None = None,
    is_fallback: bool = False,
    fallback_message: str | None = None,
) -> None:
    """
    Records interaction metadata in interaction_log.

    - role: 'user' or 'assistant'
    - position: computed automatically as MAX(position)+1 for the session
    - fallback_message: only stored when is_fallback=True (for debugging)
    """
    conn = await _get_conn()
    if not conn:
        return
    try:
        session_uuid = uuid.UUID(session_id)

        # Auto-calculate position to correctly track multi-turn conversations
        position = await conn.fetchval("""
            SELECT COALESCE(MAX(position), 0) + 1
            FROM interaction_log
            WHERE session_id = $1
        """, session_uuid)

        await conn.execute("""
            INSERT INTO interaction_log (
                session_id, position, role,
                detected_intent,
                is_fallback, fallback_message,
                response_time_ms,
                tokens_input, tokens_output,
                created_at
            ) VALUES (
                $1, $2, $3,
                $4,
                $5, $6,
                $7,
                $8, $9,
                NOW()
            )
        """,
            session_uuid, position, role,
            detected_intent,
            is_fallback, fallback_message if is_fallback else None,
            response_ms,
            tokens_in, tokens_out,
        )
        logger.debug(f"[db_writer] log_interaction OK — session={session_id} role={role} pos={position}")
    except Exception as e:
        logger.error(f"[db_writer] log_interaction failed (session={session_id}, role={role}): {e}")
    finally:
        await conn.close()


# ─── close_session ──────────────────────────────────────────────────────────

async def close_session(
    session_id: str,
    resolution_type: str = "self_service",  # "self_service" | "timeout" | "abandoned"
) -> None:
    """
    Explicitly closes a session by setting ended_at, duration_seconds, and status='resolved'.

    NOTE: This is NOT called automatically after each message anymore.
    Sessions are now closed lazily:
      - 'abandoned':  set by upsert_session when a new message arrives after 24h.
      - virtual 'abandoned': computed by v_sessions view for sessions with no follow-up.
    This function is reserved for explicit business-logic closes (e.g. user says goodbye).

    Only acts if the session is in status='active' (idempotent).
    """
    conn = await _get_conn()
    if not conn:
        return
    try:
        session_uuid = uuid.UUID(session_id)
        await conn.execute("""
            UPDATE sessions SET
                status           = 'resolved',
                resolution_type  = $2,
                is_resolved      = ($2 = 'self_service'),
                ended_at         = NOW(),
                duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER,
                updated_at       = NOW()
            WHERE id = $1
              AND status = 'active'
        """, session_uuid, resolution_type)
        logger.debug(f"[db_writer] close_session OK — id={session_id} type={resolution_type}")
    except Exception as e:
        logger.error(f"[db_writer] close_session failed (id={session_id}): {e}")
    finally:
        await conn.close()
