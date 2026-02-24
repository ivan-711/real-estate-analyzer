#!/usr/bin/env python3
"""Seed market_snapshots from Zillow Research CSV data.

Downloads ZHVI (home values) and ZORI (rent index) CSVs from Zillow Research,
filters for Midwest zip codes, and upserts the most recent month's data into
the market_snapshots table.

Usage:
    PYTHONPATH=backend python scripts/seed_market_data.py

    # With local CSV files (avoids downloading):
    PYTHONPATH=backend python scripts/seed_market_data.py \\
        --zhvi-file /path/to/Zip_zhvi.csv \\
        --zori-file /path/to/Zip_zori.csv
"""

from __future__ import annotations

import argparse
import asyncio
import io
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

# Ensure backend/ is on the path so app modules can be imported.
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx
import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

ZHVI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/"
    "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)
ZORI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/"
    "Zip_zori_uc_sfrcondomfr_sm_month.csv"
)

# Midwest zip code ranges: (start, end inclusive)
MIDWEST_ZIP_RANGES = [
    (53000, 54999),  # Wisconsin
    (60000, 62999),  # Illinois
    (48000, 49999),  # Michigan
    (55000, 56999),  # Minnesota
    (46000, 47999),  # Indiana
    (43000, 45999),  # Ohio
]

STATE_LABELS = {
    (53000, 54999): "WI",
    (60000, 62999): "IL",
    (48000, 49999): "MI",
    (55000, 56999): "MN",
    (46000, 47999): "IN",
    (43000, 45999): "OH",
}


def _is_midwest_zip(zip_str: str) -> bool:
    try:
        z = int(str(zip_str).zfill(5)[:5])
    except (ValueError, TypeError):
        return False
    return any(lo <= z <= hi for lo, hi in MIDWEST_ZIP_RANGES)


def _state_for_zip(zip_str: str) -> str:
    try:
        z = int(str(zip_str).zfill(5)[:5])
    except (ValueError, TypeError):
        return ""
    for (lo, hi), state in STATE_LABELS.items():
        if lo <= z <= hi:
            return state
    return ""


def _safe_decimal(val: object) -> Optional[Decimal]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return Decimal(str(val))
    except InvalidOperation:
        return None


def _find_latest_date_column(df: pd.DataFrame) -> Optional[str]:
    """Return the rightmost column name that looks like a YYYY-MM-DD date."""
    date_cols = [c for c in df.columns if len(str(c)) == 10 and str(c)[4] == "-"]
    if not date_cols:
        return None
    return sorted(date_cols)[-1]


async def _download_csv(url: str) -> Optional[pd.DataFrame]:
    print(f"  Downloading {url} ...")
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        return pd.read_csv(io.BytesIO(response.content), dtype={"RegionName": str})
    except Exception as exc:
        print(f"  WARNING: Failed to download {url}: {exc}")
        return None


def _load_local_csv(path: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(path, dtype={"RegionName": str})
    except Exception as exc:
        print(f"  WARNING: Failed to read {path}: {exc}")
        return None


async def seed(
    zhvi_path: Optional[str],
    zori_path: Optional[str],
    database_url: str,
) -> None:
    # Load ZHVI
    if zhvi_path:
        print(f"Loading ZHVI from local file: {zhvi_path}")
        zhvi_df = _load_local_csv(zhvi_path)
    else:
        zhvi_df = await _download_csv(ZHVI_URL)

    # Load ZORI
    if zori_path:
        print(f"Loading ZORI from local file: {zori_path}")
        zori_df = _load_local_csv(zori_path)
    else:
        zori_df = await _download_csv(ZORI_URL)

    if zhvi_df is None and zori_df is None:
        print("ERROR: Both ZHVI and ZORI sources failed. No data to insert.")
        sys.exit(1)

    # Build a dict: zip_code -> {median_home_value, snapshot_date}
    zhvi_data: dict[str, dict] = {}
    if zhvi_df is not None:
        latest_col = _find_latest_date_column(zhvi_df)
        if latest_col:
            print(f"ZHVI latest date column: {latest_col}")
            for _, row in zhvi_df.iterrows():
                zip_str = str(row.get("RegionName", "")).zfill(5)
                if not _is_midwest_zip(zip_str):
                    continue
                zhvi_data[zip_str] = {
                    "median_home_value": _safe_decimal(row.get(latest_col)),
                    "snapshot_date": latest_col,
                }

    # Build a dict: zip_code -> {median_rent, snapshot_date}
    zori_data: dict[str, dict] = {}
    if zori_df is not None:
        latest_col = _find_latest_date_column(zori_df)
        if latest_col:
            print(f"ZORI latest date column: {latest_col}")
            for _, row in zori_df.iterrows():
                zip_str = str(row.get("RegionName", "")).zfill(5)
                if not _is_midwest_zip(zip_str):
                    continue
                zori_data[zip_str] = {
                    "median_rent": _safe_decimal(row.get(latest_col)),
                    "snapshot_date": latest_col,
                }

    # Merge: union of all zip codes from either source.
    all_zips = set(zhvi_data.keys()) | set(zori_data.keys())
    print(f"Processing {len(all_zips)} Midwest zip codes...")

    # Group by state for progress reporting.
    state_counts: dict[str, int] = {}
    rows: list[dict] = []
    for zip_code in all_zips:
        zhvi = zhvi_data.get(zip_code, {})
        zori = zori_data.get(zip_code, {})

        # Use the later of the two snapshot dates if both sources have data.
        snap_date_str: Optional[str] = zhvi.get("snapshot_date") or zori.get("snapshot_date")
        if snap_date_str is None:
            continue
        try:
            snap_date = date.fromisoformat(snap_date_str[:10])
        except ValueError:
            continue

        state = _state_for_zip(zip_code)
        state_counts[state] = state_counts.get(state, 0) + 1

        rows.append(
            {
                "zip_code": zip_code,
                "city": None,
                "state": state,
                "snapshot_date": snap_date,
                "median_home_value": zhvi.get("median_home_value"),
                "median_rent": zori.get("median_rent"),
                "avg_price_per_sqft": None,
                "avg_days_on_market": None,
                "inventory_count": None,
                "avg_cap_rate": None,
                "avg_vacancy_rate": None,
                "rent_to_price_ratio": None,
                "yoy_appreciation_pct": None,
                "population_growth_pct": None,
                "data_source": "zillow_research",
                "raw_response": None,
            }
        )

    if not rows:
        print("No rows to insert.")
        return

    # Ensure asyncpg driver is used.
    if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, future=True, poolclass=NullPool)

    # Import model so metadata is registered.
    from app.models.market import MarketSnapshot  # noqa: F401

    chunk_size = 500
    total_inserted = 0
    async with engine.begin() as conn:
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(MarketSnapshot.__table__).values(chunk)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_market_snapshot",
                set_={
                    "median_home_value": stmt.excluded.median_home_value,
                    "median_rent": stmt.excluded.median_rent,
                    "city": stmt.excluded.city,
                },
            )
            await conn.execute(stmt)
            total_inserted += len(chunk)

    await engine.dispose()

    for state, count in sorted(state_counts.items()):
        print(f"  Inserted {count} rows for state {state or '??'}")
    print(f"Done. Upserted {total_inserted} total rows.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed market_snapshots from Zillow CSV data.")
    parser.add_argument("--zhvi-file", help="Local path to ZHVI CSV (skips download)")
    parser.add_argument("--zori-file", help="Local path to ZORI CSV (skips download)")
    args = parser.parse_args()

    from app.config import settings

    db_url = (settings.database_url or "").strip()
    if not db_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)

    asyncio.run(seed(args.zhvi_file, args.zori_file, db_url))


if __name__ == "__main__":
    main()
