from __future__ import annotations

from typing import AsyncGenerator

from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Use aiosqlite for SQLite async support (Railway fallback)
_database_url = settings.database_url
if _database_url.startswith("sqlite://"):
    _database_url = _database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

# SQLAlchemy 2.0 async engine
engine = create_async_engine(
    _database_url,
    echo=settings.is_development,
    future=True,
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
