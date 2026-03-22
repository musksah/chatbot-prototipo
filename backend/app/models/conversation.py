"""
Cootradecun Chatbot - Conversation Model

Unified message table (v4.0 schema).
Mirrors the model in corvusbot-dashboard for shared DB access.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    String, Integer, Boolean, Text, DateTime,
    ForeignKey, Index, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conv_session_pos", "session_id", "position"),
        {"extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    wa_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    user_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    message_type: Mapped[str | None] = mapped_column(String(50), default="text")
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    detected_intent: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tenant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fallback_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_input: Mapped[int | None] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True,
    )
