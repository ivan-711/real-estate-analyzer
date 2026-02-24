from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MarketSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    zip_code: str
    city: Optional[str] = None
    state: str
    snapshot_date: date
    median_home_value: Optional[Decimal] = None
    median_rent: Optional[Decimal] = None
    avg_price_per_sqft: Optional[Decimal] = None
    avg_days_on_market: Optional[int] = None
    inventory_count: Optional[int] = None
    avg_cap_rate: Optional[Decimal] = None
    avg_vacancy_rate: Optional[Decimal] = None
    rent_to_price_ratio: Optional[Decimal] = None
    yoy_appreciation_pct: Optional[Decimal] = None
    population_growth_pct: Optional[Decimal] = None
    data_source: Optional[str] = None
    created_at: datetime


class MarketHistoryResponse(BaseModel):
    zip_code: str
    snapshots: list[MarketSnapshotResponse]
