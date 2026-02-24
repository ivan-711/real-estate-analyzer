"""
Tests for market data API endpoints.

All RentCast calls are mocked — the real API is never hit.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import MarketSnapshot


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def market_snapshot_factory(db_session: AsyncSession):
    """Factory for creating MarketSnapshot rows directly in the test DB."""

    async def _create(
        zip_code: str = "53081",
        state: str = "WI",
        city: str | None = "Sheboygan",
        snapshot_date: date | None = None,
        median_home_value: Decimal | None = Decimal("215000.00"),
        median_rent: Decimal | None = Decimal("1550.00"),
        avg_vacancy_rate: Decimal | None = Decimal("5.50"),
        data_source: str = "rentcast",
    ) -> MarketSnapshot:
        snap = MarketSnapshot(
            zip_code=zip_code,
            state=state,
            city=city,
            snapshot_date=snapshot_date or date.today(),
            median_home_value=median_home_value,
            median_rent=median_rent,
            avg_vacancy_rate=avg_vacancy_rate,
            data_source=data_source,
        )
        db_session.add(snap)
        await db_session.commit()
        await db_session.refresh(snap)
        return snap

    return _create


def _mock_rentcast_stats(zip_code: str = "53081") -> dict:
    """Return a normalized market stats dict matching _normalize_market_stats output."""
    return {
        "zip_code": zip_code,
        "city": "Sheboygan",
        "state": "WI",
        "median_home_value": 220000,
        "median_rent": 1600,
        "avg_vacancy_rate": 5.2,
        "yoy_appreciation_pct": 3.1,
        "population_growth_pct": 0.4,
        "rent_to_price_ratio": 0.0073,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/markets/{zip_code}
# ---------------------------------------------------------------------------


async def test_get_market_snapshot_from_db(
    client: AsyncClient,
    market_snapshot_factory,
) -> None:
    """GET /{zip} returns 200 when RentCast is unavailable but DB has a row."""
    from app.integrations.rentcast import ExternalAPIUnavailable

    await market_snapshot_factory(zip_code="53081", median_home_value=Decimal("215000"))

    with patch(
        "app.services.market_comparator.RentCastClient",
    ) as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.get_market_stats.side_effect = ExternalAPIUnavailable("Network error")
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        response = await client.get("/api/v1/markets/53081")

    assert response.status_code == 200
    data = response.json()
    assert data["zip_code"] == "53081"
    assert float(data["median_home_value"]) == pytest.approx(215000, rel=1e-3)


async def test_get_market_snapshot_not_found(
    client: AsyncClient,
) -> None:
    """GET /{zip} with no DB data and RentCast returning 404 returns 404."""
    from app.integrations.rentcast import PropertyNotFound

    with patch(
        "app.services.market_comparator.RentCastClient",
    ) as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.get_market_stats.side_effect = PropertyNotFound("Not found")
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        response = await client.get("/api/v1/markets/99999")

    assert response.status_code == 404
    assert "99999" in response.json()["detail"]


async def test_get_market_snapshot_rentcast_fallback(
    client: AsyncClient,
    market_snapshot_factory,
) -> None:
    """GET /{zip} falls back to DB row when RentCast raises any RentCastError."""
    from app.integrations.rentcast import RentCastQuotaExhausted

    await market_snapshot_factory(
        zip_code="53202",
        city="Milwaukee",
        median_home_value=Decimal("180000"),
        data_source="zillow_research",
    )

    with patch(
        "app.services.market_comparator.RentCastClient",
    ) as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.get_market_stats.side_effect = RentCastQuotaExhausted("Quota exhausted")
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        response = await client.get("/api/v1/markets/53202")

    assert response.status_code == 200
    data = response.json()
    assert data["zip_code"] == "53202"
    assert float(data["median_home_value"]) == pytest.approx(180000, rel=1e-3)


async def test_get_market_snapshot_live_rentcast(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /{zip} with successful RentCast call persists and returns the new row."""
    with patch(
        "app.services.market_comparator.RentCastClient",
    ) as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.get_market_stats.return_value = _mock_rentcast_stats("53081")
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance

        response = await client.get("/api/v1/markets/53081")

    assert response.status_code == 200
    data = response.json()
    assert data["zip_code"] == "53081"
    assert data["data_source"] == "rentcast"
    assert float(data["median_home_value"]) == pytest.approx(220000, rel=1e-3)
    assert float(data["median_rent"]) == pytest.approx(1600, rel=1e-3)


# ---------------------------------------------------------------------------
# GET /api/v1/markets/{zip_code}/history
# ---------------------------------------------------------------------------


async def test_get_market_history(
    client: AsyncClient,
    market_snapshot_factory,
) -> None:
    """GET /{zip}/history returns snapshots ordered newest first."""
    today = date.today()
    await market_snapshot_factory(
        zip_code="53081",
        snapshot_date=today - timedelta(days=60),
        median_home_value=Decimal("200000"),
    )
    await market_snapshot_factory(
        zip_code="53081",
        snapshot_date=today - timedelta(days=30),
        median_home_value=Decimal("210000"),
        data_source="zillow_research",
    )
    await market_snapshot_factory(
        zip_code="53081",
        snapshot_date=today,
        median_home_value=Decimal("220000"),
    )

    response = await client.get("/api/v1/markets/53081/history")

    assert response.status_code == 200
    data = response.json()
    assert data["zip_code"] == "53081"
    snapshots = data["snapshots"]
    assert len(snapshots) >= 3
    # Verify descending order.
    dates = [s["snapshot_date"] for s in snapshots]
    assert dates == sorted(dates, reverse=True)


async def test_get_market_history_empty(
    client: AsyncClient,
) -> None:
    """GET /{zip}/history with no data returns 200 with empty list."""
    response = await client.get("/api/v1/markets/00000/history")

    assert response.status_code == 200
    data = response.json()
    assert data["zip_code"] == "00000"
    assert data["snapshots"] == []


# ---------------------------------------------------------------------------
# GET /api/v1/markets/compare
# ---------------------------------------------------------------------------


async def test_compare_two_zips(
    client: AsyncClient,
    market_snapshot_factory,
) -> None:
    """GET /compare with 2 zips returns one snapshot per zip."""
    await market_snapshot_factory(zip_code="53081", median_home_value=Decimal("215000"))
    await market_snapshot_factory(zip_code="53202", median_home_value=Decimal("175000"))

    response = await client.get("/api/v1/markets/compare?zips=53081,53202")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    returned_zips = {s["zip_code"] for s in data}
    assert returned_zips == {"53081", "53202"}


async def test_compare_three_zips(
    client: AsyncClient,
    market_snapshot_factory,
) -> None:
    """GET /compare with 3 zips returns one snapshot per zip."""
    await market_snapshot_factory(zip_code="53081")
    await market_snapshot_factory(zip_code="53202")
    await market_snapshot_factory(zip_code="53211")

    response = await client.get("/api/v1/markets/compare?zips=53081,53202,53211")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    returned_zips = {s["zip_code"] for s in data}
    assert returned_zips == {"53081", "53202", "53211"}


async def test_compare_missing_zip(
    client: AsyncClient,
    market_snapshot_factory,
) -> None:
    """GET /compare omits zips that have no data rather than erroring."""
    await market_snapshot_factory(zip_code="53081")
    await market_snapshot_factory(zip_code="53202")
    # 99998 has no data.

    response = await client.get("/api/v1/markets/compare?zips=53081,53202,99998")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    returned_zips = {s["zip_code"] for s in data}
    assert returned_zips == {"53081", "53202"}


async def test_compare_too_few_zips(
    client: AsyncClient,
) -> None:
    """GET /compare with 1 zip returns 400."""
    response = await client.get("/api/v1/markets/compare?zips=53081")

    assert response.status_code == 400
    assert "2" in response.json()["detail"]


async def test_compare_too_many_zips(
    client: AsyncClient,
) -> None:
    """GET /compare with 6 zips returns 400."""
    response = await client.get(
        "/api/v1/markets/compare?zips=53081,53202,53211,53403,60601,60602"
    )

    assert response.status_code == 400
    assert "5" in response.json()["detail"]
