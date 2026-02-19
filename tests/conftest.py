"""
Pytest configuration and fixtures.

Fixtures:
- client: httpx.AsyncClient (ASGITransport) so app runs in same event loop as engine
- ensure_db_schema: session-scoped async fixture that creates tables in session loop
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure backend is in path for app imports
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Set test env vars before importing app (if not already set)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the whole session so asyncpg and app share the same loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def ensure_db_schema(event_loop: asyncio.AbstractEventLoop) -> None:
    """Create database tables in the session event loop (so engine is bound to it)."""
    from app.database import Base, engine
    from app.models import Deal, Property, RefreshToken, User  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def client(ensure_db_schema: None) -> AsyncClient:
    """AsyncClient so the app runs in the same event loop as the database engine."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
