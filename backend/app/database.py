"""
Async SQLAlchemy database module.

Provides async engine and session factory for the chatbot models.
Reuses the DATABASE_URL from environment (also used by LangGraph checkpointer).
"""

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert postgresql:// to postgresql+asyncpg:// for async support
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = None
async_session_factory = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def _ensure_engine():
    """Lazily create the async engine and session factory."""
    global engine, async_session_factory
    if engine is None:
        if not ASYNC_DATABASE_URL or ASYNC_DATABASE_URL == "":
            raise RuntimeError("DATABASE_URL not configured")
        engine = create_async_engine(
            ASYNC_DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
        )
        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("✅ Async SQLAlchemy engine created")


async def get_db():
    """FastAPI dependency: yields an async database session."""
    _ensure_engine()
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all tables defined by Base metadata."""
    _ensure_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created/verified")
