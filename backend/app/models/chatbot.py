"""
Conversation model — maps to the existing `conversations` table in PostgreSQL.

This table stores all WhatsApp messages (incoming and outgoing)
for the dashboard API.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True, comment="Unique message ID (UUID or wa_message_id)")
    wa_message_id = Column(String(200), nullable=True, comment="WhatsApp message ID (wamid.*)")
    user_phone = Column(String(30), nullable=True, comment="User phone number")
    user_name = Column(String(200), nullable=True, comment="WhatsApp display name")
    session_id = Column(String(100), nullable=True, index=True, comment="Thread/session ID (e.g. wa-573001234567)")
    message = Column(Text, nullable=True, comment="Message body")
    role = Column(String(20), nullable=True, default="user", comment="'user' or 'assistant'")
    message_type = Column(String(50), nullable=True, default="text", comment="Message type: text, image, etc.")
    detected_intent = Column(String(200), nullable=True, comment="Detected intent/department")
    department = Column(String(100), nullable=True, comment="Agent/department that handled the message")
    tokens_input = Column(Integer, nullable=True, comment="Input tokens used")
    tokens_output = Column(Integer, nullable=True, comment="Output tokens used")
    response_time_ms = Column(Integer, nullable=True, comment="Response time in milliseconds")
    created_at = Column(DateTime(timezone=True), nullable=True, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_conversations_session_created", "session_id", "created_at"),
        Index("ix_conversations_user_phone", "user_phone"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, session={self.session_id}, role={self.role})>"
