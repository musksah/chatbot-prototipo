"""
Cootradecun Chatbot API - Conversations/Messages Routes

Endpoints for viewing WhatsApp message sessions and individual messages.
"""
from datetime import date
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from app.database import get_db
from app.models.chatbot import Conversation
from app.schemas.conversations import (
    SessionResponse,
    SessionListResponse,
    SessionDetailResponse,
    MessageResponse,
    MessageSearchResponse,
)
from app.api.deps import require_any_role, CurrentUser

router = APIRouter(prefix="/conversations", tags=["Conversaciones"])


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_any_role)],
    page: int = Query(1, ge=1, description="Pagina actual"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por pagina"),
    user_phone: Optional[str] = Query(None, description="Filtrar por telefono"),
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
    start_date: Optional[date] = Query(None, description="Fecha inicial"),
    end_date: Optional[date] = Query(None, description="Fecha final"),
    search: Optional[str] = Query(None, description="Buscar en mensajes"),
):
    """
    List conversation sessions, grouped by session_id.
    
    Returns a paginated list of sessions ordered by most recent activity.
    """
    # Base filters
    filters = [Conversation.session_id.isnot(None)]
    
    if user_phone:
        filters.append(Conversation.user_phone.contains(user_phone))
    if department:
        filters.append(Conversation.department == department)
    if start_date:
        filters.append(func.date(Conversation.created_at) >= start_date)
    if end_date:
        filters.append(func.date(Conversation.created_at) <= end_date)
    if search:
        filters.append(Conversation.message.ilike(f"%{search}%"))
    
    where_clause = and_(*filters) if filters else True
    
    # Count total distinct sessions
    count_query = select(
        func.count(func.distinct(Conversation.session_id))
    ).where(where_clause)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Get session summaries with aggregation
    session_query = (
        select(
            Conversation.session_id,
            Conversation.user_phone,
            func.max(Conversation.user_name).label("user_name"),
            func.count(Conversation.id).label("message_count"),
            func.min(Conversation.created_at).label("first_message_at"),
            func.max(Conversation.created_at).label("last_message_at"),
            func.max(Conversation.department).label("department"),
        )
        .where(where_clause)
        .group_by(Conversation.session_id, Conversation.user_phone)
        .order_by(desc("last_message_at"))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    
    result = await db.execute(session_query)
    rows = result.all()
    
    # Get last message preview for each session
    sessions = []
    for row in rows:
        last_msg_query = (
            select(Conversation.message)
            .where(Conversation.session_id == row.session_id)
            .order_by(desc(Conversation.created_at))
            .limit(1)
        )
        last_msg_result = await db.execute(last_msg_query)
        last_message = last_msg_result.scalar() or ""
        
        sessions.append(
            SessionResponse(
                session_id=row.session_id,
                user_phone=row.user_phone,
                user_name=row.user_name,
                message_count=row.message_count,
                last_message_preview=last_message[:100],
                first_message_at=row.first_message_at,
                last_message_at=row.last_message_at,
                department=row.department,
            )
        )
    
    return SessionListResponse(
        sessions=sessions,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_messages(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_any_role)],
):
    """
    Get all messages for a specific session, ordered chronologically.
    """
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.asc())
    )
    messages = result.scalars().all()
    
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesion no encontrada",
        )
    
    user_phone = messages[0].user_phone
    user_name = next(
        (m.user_name for m in messages if m.user_name), None
    )
    
    return SessionDetailResponse(
        session_id=session_id,
        user_phone=user_phone,
        user_name=user_name,
        messages=[MessageResponse.model_validate(m) for m in messages],
        total_messages=len(messages),
    )


@router.get("/search", response_model=MessageSearchResponse)
async def search_messages(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_any_role)],
    q: str = Query(..., min_length=2, description="Texto a buscar"),
    page: int = Query(1, ge=1, description="Pagina actual"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por pagina"),
):
    """
    Search messages by text content.
    """
    search_filter = Conversation.message.ilike(f"%{q}%")
    
    count_result = await db.execute(
        select(func.count(Conversation.id)).where(search_filter)
    )
    total = count_result.scalar() or 0
    
    result = await db.execute(
        select(Conversation)
        .where(search_filter)
        .order_by(desc(Conversation.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()
    
    return MessageSearchResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
    )
