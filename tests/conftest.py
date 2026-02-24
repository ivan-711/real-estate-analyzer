"""
Pytest configuration and shared fixtures.

This test setup:
- uses TEST_DATABASE_URL when provided, otherwise DATABASE_URL
- wraps each test in a rollback-safe transaction
- overrides FastAPI get_db dependency so API tests use the isolated session
"""

from __future__ import annotations

import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import AsyncGenerator, Dict

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

# Ensure backend is in path for app imports
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Set required test env vars before importing app modules.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Choose test DB URL, preferring dedicated TEST_DATABASE_URL when available."""
    from app.config import settings

    return (settings.test_database_url or settings.database_url).strip()


@pytest.fixture(scope="session")
async def test_engine(test_database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create test engine and ensure schema exists.

    If TEST_DATABASE_URL is provided, tables are dropped at session end.
    """
    from app.config import settings
    from app.database import Base
    from app.models import (  # noqa: F401
        ChatMessage,
        ChatSession,
        Deal,
        Property,
        RefreshToken,
        User,
    )

    engine = create_async_engine(
        test_database_url,
        echo=settings.is_development,
        future=True,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    if settings.test_database_url:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped transactional session.

    Uses a connection-level outer transaction plus per-session savepoints, so
    endpoint code can call commit() while each test is still rolled back.
    """
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """ASGI test client with get_db dependency overridden to use isolated test session."""
    from app.database import get_db
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def unique_email() -> str:
    """Generate a unique email for each test fixture invocation."""
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
async def test_user(db_session: AsyncSession, unique_email: str):
    """Create and return a test user with a hashed password."""
    from app.middleware.auth import hash_password
    from app.models.user import User

    user = User(
        email=unique_email,
        password_hash=hash_password("password123"),
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user) -> str:
    """Return a valid JWT access token for test_user."""
    from app.middleware.auth import create_access_token

    return create_access_token(test_user.id)


@pytest.fixture
def auth_headers(test_user_token: str) -> dict[str, str]:
    """Authorization headers for authenticated requests as test_user."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def sheboygan_property_payload() -> dict:
    """Canonical Sheboygan sample payload for property creation."""
    return {
        "address": "1515 N 7th St",
        "city": "Sheboygan",
        "state": "WI",
        "zip_code": "53081",
        "county": "Sheboygan",
        "property_type": "duplex",
        "num_units": 2,
        "bedrooms": 5,
        "bathrooms": 2.0,
        "square_footage": 2330,
        "lot_size": 4356,
        "year_built": 1900,
    }


@pytest.fixture
async def test_property(
    db_session: AsyncSession, test_user, sheboygan_property_payload: dict
):
    """Create and return a Sheboygan test property owned by test_user."""
    from app.models.property import Property

    property_ = Property(
        user_id=test_user.id,
        **sheboygan_property_payload,
    )
    db_session.add(property_)
    await db_session.commit()
    await db_session.refresh(property_)
    return property_


@pytest.fixture
def sheboygan_deal_payload(test_property) -> dict:
    """Realistic Sheboygan duplex deal input payload for API deal creation."""
    return {
        "property_id": str(test_property.id),
        "deal_name": "Sheboygan Duplex",
        "purchase_price": "220000",
        "closing_costs": "6600",
        "rehab_costs": "5000",
        "down_payment_pct": "20",
        "loan_amount": "176000",
        "interest_rate": "7.0",
        "loan_term_years": 30,
        "monthly_mortgage": "1171",
        "gross_monthly_rent": "1800",
        "other_monthly_income": "0",
        "property_tax_monthly": "320",
        "insurance_monthly": "120",
        "vacancy_rate_pct": "5",
        "maintenance_rate_pct": "5",
        "management_fee_pct": "10",
        "hoa_monthly": "0",
        "utilities_monthly": "0",
    }


@pytest.fixture
async def test_deal(db_session: AsyncSession, test_user, test_property):
    """Create and return a realistic Sheboygan deal linked to test_property."""
    from app.models.deal import Deal

    deal = Deal(
        property_id=test_property.id,
        user_id=test_user.id,
        deal_name="Sheboygan Duplex",
        purchase_price=Decimal("220000"),
        closing_costs=Decimal("6600"),
        rehab_costs=Decimal("5000"),
        down_payment_pct=Decimal("20"),
        loan_amount=Decimal("176000"),
        interest_rate=Decimal("7.0"),
        loan_term_years=30,
        monthly_mortgage=Decimal("1171"),
        gross_monthly_rent=Decimal("1800"),
        other_monthly_income=Decimal("0"),
        property_tax_monthly=Decimal("320"),
        insurance_monthly=Decimal("120"),
        vacancy_rate_pct=Decimal("5"),
        maintenance_rate_pct=Decimal("5"),
        management_fee_pct=Decimal("10"),
        hoa_monthly=Decimal("0"),
        utilities_monthly=Decimal("0"),
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)
    return deal


@pytest.fixture
async def create_user(db_session: AsyncSession):
    """Factory fixture for creating additional users (e.g., User B in isolation tests)."""
    from app.middleware.auth import create_access_token, hash_password
    from app.models.user import User

    async def _create_user(
        *,
        email: str | None = None,
        full_name: str = "Test User",
        password: str = "password123",
    ):
        user = User(
            email=email or f"test-{uuid.uuid4().hex[:12]}@example.com",
            password_hash=hash_password(password),
            full_name=full_name,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        token = create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}
        return user, token, headers

    return _create_user


@pytest.fixture
def sample_rentcast_property_response() -> Dict[str, object]:
    """Hardcoded sample payload matching the normalized lookup response shape."""
    return {
        "address": "1515 N 7th St",
        "city": "Sheboygan",
        "state": "WI",
        "zip_code": "53081",
        "county": "Sheboygan",
        "property_type": "duplex",
        "num_units": 2,
        "bedrooms": 5,
        "bathrooms": 2.0,
        "square_footage": 2330,
        "lot_size": 4356,
        "year_built": 1900,
        "rentcast_id": "sample-rentcast-id-1515-n-7th",
        "estimated_value": 220000,
        "rent_estimate_monthly": 1800,
        "rent_estimate_low": 1650,
        "rent_estimate_high": 1950,
        "rent_estimate_confidence": 0.84,
    }
