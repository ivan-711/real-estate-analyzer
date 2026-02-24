from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.rentcast import RentCastClient, RentCastError
from app.models.market import MarketSnapshot

logger = logging.getLogger(__name__)


def _safe_decimal(value: object) -> Optional[Decimal]:
    """Convert a value to Decimal, returning None for falsy or non-numeric values."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


async def get_market_snapshot(
    zip_code: str,
    db: AsyncSession,
) -> Optional[MarketSnapshot]:
    """Return the current market snapshot for a zip code.

    Attempts a live RentCast lookup first, persists the result to DB, and returns
    the saved row. Falls back to the most recent existing DB row if RentCast fails.
    Returns None only when both RentCast and DB have no data.
    """
    today = date.today()

    try:
        client = RentCastClient()
        stats = await client.get_market_stats(zip_code)
        await client.close()

        # Check if a row for today already exists to avoid duplicate inserts.
        existing_result = await db.execute(
            select(MarketSnapshot).where(
                MarketSnapshot.zip_code == zip_code,
                MarketSnapshot.snapshot_date == today,
                MarketSnapshot.data_source == "rentcast",
            )
        )
        snapshot = existing_result.scalar_one_or_none()

        if snapshot is None:
            snapshot = MarketSnapshot(
                zip_code=zip_code,
                city=stats.get("city"),
                state=stats.get("state") or "",
                snapshot_date=today,
                median_home_value=_safe_decimal(stats.get("median_home_value")),
                median_rent=_safe_decimal(stats.get("median_rent")),
                avg_vacancy_rate=_safe_decimal(stats.get("avg_vacancy_rate")),
                yoy_appreciation_pct=_safe_decimal(stats.get("yoy_appreciation_pct")),
                population_growth_pct=_safe_decimal(stats.get("population_growth_pct")),
                rent_to_price_ratio=_safe_decimal(stats.get("rent_to_price_ratio")),
                data_source="rentcast",
                raw_response=None,
            )
            db.add(snapshot)
            await db.commit()
            await db.refresh(snapshot)
        else:
            # Row already exists for today; update numeric fields in case cache was stale.
            snapshot.median_home_value = _safe_decimal(stats.get("median_home_value"))
            snapshot.median_rent = _safe_decimal(stats.get("median_rent"))
            snapshot.avg_vacancy_rate = _safe_decimal(stats.get("avg_vacancy_rate"))
            snapshot.yoy_appreciation_pct = _safe_decimal(stats.get("yoy_appreciation_pct"))
            snapshot.population_growth_pct = _safe_decimal(stats.get("population_growth_pct"))
            snapshot.rent_to_price_ratio = _safe_decimal(stats.get("rent_to_price_ratio"))
            await db.commit()
            await db.refresh(snapshot)

        return snapshot

    except RentCastError as exc:
        logger.warning(
            "RentCast lookup failed for zip=%s error=%s — falling back to DB",
            zip_code,
            exc.detail,
        )

    # Fallback: most recent DB row for this zip regardless of source.
    fallback_result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.zip_code == zip_code)
        .order_by(MarketSnapshot.snapshot_date.desc())
        .limit(1)
    )
    return fallback_result.scalar_one_or_none()


async def get_market_history(
    zip_code: str,
    db: AsyncSession,
) -> list[MarketSnapshot]:
    """Return all historical snapshots for a zip code, newest first."""
    result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.zip_code == zip_code)
        .order_by(MarketSnapshot.snapshot_date.desc())
    )
    return list(result.scalars().all())


async def get_market_comparison(
    zip_codes: list[str],
    db: AsyncSession,
) -> list[MarketSnapshot]:
    """Return the most recent snapshot for each zip code that has data."""
    snapshots: list[MarketSnapshot] = []
    for zip_code in zip_codes:
        result = await db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.zip_code == zip_code)
            .order_by(MarketSnapshot.snapshot_date.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            snapshots.append(row)
    return snapshots
