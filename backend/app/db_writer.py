"""
db_writer.py — Schema v4.0 Write Layer

Encapsulates all direct writes to the v4.0 schema tables:
  - whatsapp_contacts
  - sessions
  - conversations  (unified: replaces legacy conversations + interaction_log)

Uses asyncpg directly (bypassing SQLAlchemy) to maintain independence
from the main engine and minimize the risk of interference with the
chatbot flow.

Connection management: uses an asyncpg.Pool (lazy-initialized) for
efficient connection reuse. Each function acquires and releases a
connection from the pool via `async with`.

Error handling: each function has its own try/except that logs the error
without propagating it — never blocks the chatbot flow.

Session window:
  A session spans 24 hours from the first message. If the user writes again
  within that window, the same session is reused. After 24h, the old session
  is marked 'abandoned' and a new one is created.
  Sessions that expire without a follow-up are handled by the effective_status
  property on the SQLAlchemy model, which computes the status at read time.
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


# ─── Connection Pool ────────────────────────────────────────────────────────

_pool: asyncpg.Pool | None = None


async def _get_pool() -> asyncpg.Pool | None:
    """Returns a shared asyncpg connection pool (lazy init), or None if unconfigured."""
    global _pool
    if not _DATABASE_URL:
        logger.warning("[db_writer] DATABASE_URL not configured — v4.0 writes disabled")
        return None
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(_DATABASE_URL, min_size=1, max_size=5)
            logger.info("[db_writer] Connection pool created (min=1, max=5)")
        except Exception as e:
            logger.error(f"[db_writer] Could not create connection pool: {e}")
            return None
    return _pool


async def close_pool() -> None:
    """Closes the connection pool. Call on app shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("[db_writer] Connection pool closed")


# ─── whatsapp_contacts ──────────────────────────────────────────────────────

async def upsert_contact(phone: str, name: str | None = None) -> str | None:
    """
    Creates or updates a contact in whatsapp_contacts.

    - New contact: inserts the record with total_sessions=0 (session count
      is incremented separately by upsert_session when a new session is created).
    - Existing contact: updates name and last_seen_at.

    Returns the contact UUID (str), or None on failure.
    """
    pool = await _get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO whatsapp_contacts (phone, name, first_seen_at, last_seen_at)
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT (phone) DO UPDATE
                    SET name         = COALESCE($2, whatsapp_contacts.name),
                        last_seen_at = NOW(),
                        updated_at   = NOW()
                RETURNING id::TEXT
            """, phone, name)
            contact_id = row["id"] if row else None
            if contact_id:
                logger.debug(f"[db_writer] upsert_contact OK — phone={phone} id={contact_id}")
            return contact_id
    except Exception as e:
        logger.error(f"[db_writer] upsert_contact failed (phone={phone}): {e}")
        return None


# ─── sessions ───────────────────────────────────────────────────────────────

async def upsert_session(contact_id: str, session_key: str) -> str | None:
    """
    Returns the active session ID for the given contact within the last 24 hours.

    - If an active session exists started less than 24h ago → return its ID (conversation continues).
    - Otherwise → mark the previous active session as 'abandoned', create a new one,
      and increment total_sessions + is_returning on the contact.

    Returns the session UUID (str), or None on failure.
    """
    pool = await _get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
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

            # 4. Increment total_sessions + is_returning on the contact
            if session_id:
                await conn.execute("""
                    UPDATE whatsapp_contacts
                    SET total_sessions = total_sessions + 1,
                        is_returning   = (total_sessions >= 1),
                        updated_at     = NOW()
                    WHERE id = $1
                """, contact_uuid)
                logger.debug(f"[db_writer] upsert_session new — contact={contact_id} session={session_id} key={unique_key}")

            return session_id

    except Exception as e:
        logger.error(f"[db_writer] upsert_session failed (contact={contact_id}): {e}")
        return None


# ─── conversations (unified messages) ──────────────────────────────────────

async def save_conversation(
    session_id: str,
    role: str,
    message: str,
    *,
    user_phone: str | None = None,
    user_name: str | None = None,
    wa_message_id: str | None = None,
    detected_intent: str | None = None,
    department: str | None = None,
    tenant: str | None = None,
    is_fallback: bool = False,
    response_time_ms: int | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> None:
    """
    Writes a single message to the conversations table (unified).

    Replaces both the legacy save_message() and the v3.0 log_interaction().
    Stores the full message content plus analytics metadata (intent, fallback,
    response time, tokens, etc.).

    Position is auto-calculated as MAX(position)+1 for the session.
    """
    pool = await _get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            session_uuid = uuid.UUID(session_id)

            # Auto-calculate position
            position = await conn.fetchval("""
                SELECT COALESCE(MAX(position), 0) + 1
                FROM conversations
                WHERE session_id = $1
            """, session_uuid)

            await conn.execute("""
                INSERT INTO conversations (
                    session_id, wa_message_id, user_phone, user_name,
                    message, role, message_type, position,
                    detected_intent, department, tenant,
                    is_fallback, fallback_message,
                    response_time_ms, tokens_input, tokens_output,
                    created_at
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, 'text', $7,
                    $8, $9, $10,
                    $11, $12,
                    $13, $14, $15,
                    NOW()
                )
            """,
                session_uuid, wa_message_id, user_phone, user_name,
                message, role, position,
                detected_intent, department, tenant,
                is_fallback, message if is_fallback else None,
                response_time_ms, tokens_in, tokens_out,
            )
            logger.debug(
                f"[db_writer] save_conversation OK — session={session_id} "
                f"role={role} pos={position}"
            )
    except Exception as e:
        logger.error(f"[db_writer] save_conversation failed (session={session_id}, role={role}): {e}")


# ─── mark_resolution ────────────────────────────────────────────────────────

async def mark_resolution(session_id: str) -> None:
    """
    Marks had_resolution=TRUE on a session.

    Call this when the bot detects that it resolved the user's request
    (e.g. intent=farewell, or agent completes a workflow successfully).
    This allows the effective_status logic to classify expired sessions
    as 'resolved' instead of 'abandoned'.
    """
    pool = await _get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            session_uuid = uuid.UUID(session_id)
            await conn.execute("""
                UPDATE sessions
                SET had_resolution = TRUE,
                    updated_at     = NOW()
                WHERE id = $1
                  AND status = 'active'
            """, session_uuid)
            logger.debug(f"[db_writer] mark_resolution OK — session={session_id}")
    except Exception as e:
        logger.error(f"[db_writer] mark_resolution failed (session={session_id}): {e}")


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
      - virtual status: computed by effective_status property at read time.
    This function is reserved for explicit business-logic closes (e.g. user says goodbye).

    Only acts if the session is in status='active' (idempotent).
    """
    pool = await _get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            session_uuid = uuid.UUID(session_id)
            await conn.execute("""
                UPDATE sessions SET
                    status           = 'resolved',
                    resolution_type  = $2,
                    is_resolved      = ($2 = 'self_service'),
                    had_resolution   = TRUE,
                    ended_at         = NOW(),
                    duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER,
                    updated_at       = NOW()
                WHERE id = $1
                  AND status = 'active'
            """, session_uuid, resolution_type)
            logger.debug(f"[db_writer] close_session OK — id={session_id} type={resolution_type}")
    except Exception as e:
        logger.error(f"[db_writer] close_session failed (id={session_id}): {e}")


# ─── update_session_stats ────────────────────────────────────────────────────

async def update_session_stats(
    session_id: str,
    *,
    user_messages_delta: int = 0,
    bot_messages_delta: int = 0,
    fallback_delta: int = 0,
    primary_intent: str | None = None,
    tokens_input_delta: int = 0,
    tokens_output_delta: int = 0,
    estimated_cost_delta: float = 0.0,
) -> None:
    """
    Incremental UPDATE of session counters after each conversation turn.

    Called once per bot response in /chat/fake_whatsapp to keep sessions
    table up-to-date without blocking the chatbot flow.

    - Counters (messages, tokens, fallback) are incremented atomically.
    - primary_intent is only written when a non-None value is provided.
    - estimated_cost_usd accumulates across all turns of the session.
    """
    pool = await _get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            session_uuid = uuid.UUID(session_id)

            if primary_intent is not None:
                await conn.execute("""
                    UPDATE sessions SET
                        total_messages      = total_messages      + $2,
                        user_messages       = user_messages       + $3,
                        bot_messages        = bot_messages        + $4,
                        fallback_count      = fallback_count      + $5,
                        primary_intent      = $6,
                        total_tokens_input  = total_tokens_input  + $7,
                        total_tokens_output = total_tokens_output + $8,
                        estimated_cost_usd  = estimated_cost_usd  + $9,
                        updated_at          = NOW()
                    WHERE id = $1
                """,
                    session_uuid,
                    user_messages_delta + bot_messages_delta,
                    user_messages_delta,
                    bot_messages_delta,
                    fallback_delta,
                    primary_intent,
                    tokens_input_delta,
                    tokens_output_delta,
                    estimated_cost_delta,
                )
            else:
                await conn.execute("""
                    UPDATE sessions SET
                        total_messages      = total_messages      + $2,
                        user_messages       = user_messages       + $3,
                        bot_messages        = bot_messages        + $4,
                        fallback_count      = fallback_count      + $5,
                        total_tokens_input  = total_tokens_input  + $6,
                        total_tokens_output = total_tokens_output + $7,
                        estimated_cost_usd  = estimated_cost_usd  + $8,
                        updated_at          = NOW()
                    WHERE id = $1
                """,
                    session_uuid,
                    user_messages_delta + bot_messages_delta,
                    user_messages_delta,
                    bot_messages_delta,
                    fallback_delta,
                    tokens_input_delta,
                    tokens_output_delta,
                    estimated_cost_delta,
                )

            logger.debug(
                f"[db_writer] update_session_stats OK — session={session_id} "
                f"user+={user_messages_delta} bot+={bot_messages_delta} "
                f"fallback+={fallback_delta} intent={primary_intent}"
            )
    except Exception as e:
        logger.error(f"[db_writer] update_session_stats failed (session={session_id}): {e}")


# ─── increment_contact_messages ─────────────────────────────────────────────

async def increment_contact_messages(phone: str, count: int = 1) -> None:
    """
    Increments total_messages counter for a WhatsApp contact.

    Called after each full turn (user + bot) in /chat/fake_whatsapp.
    Uses an atomic UPDATE to avoid race conditions.
    """
    pool = await _get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE whatsapp_contacts
                SET total_messages = total_messages + $2,
                    updated_at     = NOW()
                WHERE phone = $1
            """, phone, count)
            logger.debug(f"[db_writer] increment_contact_messages OK — phone={phone} +{count}")
    except Exception as e:
        logger.error(f"[db_writer] increment_contact_messages failed (phone={phone}): {e}")
