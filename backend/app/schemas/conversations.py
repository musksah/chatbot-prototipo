"""
Pydantic schemas for WhatsApp conversations/messages viewing (v4.0).
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class MessageResponse(BaseModel):
    """Single message in a conversation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    user_phone: Optional[str] = None
    user_name: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None
    wa_message_id: Optional[str] = None
    message_type: Optional[str] = None
    position: Optional[int] = None
    department: Optional[str] = None
    tenant: Optional[str] = None
    detected_intent: Optional[str] = None
    is_fallback: bool = False
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    response_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None


class SessionResponse(BaseModel):
    """Summary of a conversation session."""
    session_id: str
    user_phone: Optional[str] = None
    user_name: Optional[str] = None
    message_count: int
    last_message_preview: str
    first_message_at: datetime
    last_message_at: datetime
    department: Optional[str] = None


class SessionListResponse(BaseModel):
    """Paginated list of sessions."""
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int


class SessionDetailResponse(BaseModel):
    """Full session with all messages."""
    session_id: str
    user_phone: Optional[str] = None
    user_name: Optional[str] = None
    messages: List[MessageResponse]
    total_messages: int


class MessageSearchResponse(BaseModel):
    """Paginated search results."""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
