from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PropertyCreate(BaseModel):
    """Fields for creating a property."""

    address: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., max_length=10)
    county: Optional[str] = Field(None, max_length=100)
    property_type: str = Field(..., max_length=50)
    num_units: int = Field(1, ge=1)
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[int] = Field(None, ge=0)
    lot_size: Optional[int] = Field(None, ge=0)
    year_built: Optional[int] = Field(None, ge=1800, le=2100)


class PropertyUpdate(BaseModel):
    """All fields optional for partial updates."""

    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    county: Optional[str] = Field(None, max_length=100)
    property_type: Optional[str] = Field(None, max_length=50)
    num_units: Optional[int] = Field(None, ge=1)
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[int] = Field(None, ge=0)
    lot_size: Optional[int] = Field(None, ge=0)
    year_built: Optional[int] = Field(None, ge=1800, le=2100)


class PropertyResponse(BaseModel):
    """Property as returned by API (includes id and timestamps)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    address: str
    city: str
    state: str
    zip_code: str
    county: Optional[str]
    property_type: str
    num_units: int
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_footage: Optional[int]
    lot_size: Optional[int]
    year_built: Optional[int]
    rentcast_id: Optional[str]
    mashvisor_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class PropertyLookupRequest(BaseModel):
    """Request payload for RentCast property lookup."""

    address: str = Field(..., min_length=5, max_length=255)


class PropertyLookupResponse(BaseModel):
    """Normalized property lookup payload used to pre-fill deal/property forms."""

    address: str
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    county: Optional[str]
    property_type: Optional[str]
    num_units: Optional[int]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_footage: Optional[int]
    lot_size: Optional[int]
    year_built: Optional[int]
    rentcast_id: Optional[str]
    rent_estimate_monthly: Optional[float]
    rent_estimate_low: Optional[float]
    rent_estimate_high: Optional[float]
    rent_estimate_confidence: Optional[float]
    estimated_value: Optional[float] = None
