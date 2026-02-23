from __future__ import annotations

import uuid

from app.database import get_db
from app.integrations.rentcast import (
    SAMPLE_LOOKUP_RESPONSE,
    PropertyNotFound,
    RentCastClient,
)
from app.middleware.auth import get_current_user
from app.models.property import Property
from app.models.user import User
from app.schemas.property import (
    PropertyCreate,
    PropertyLookupRequest,
    PropertyLookupResponse,
    PropertyResponse,
    PropertyUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/properties", tags=["properties"])


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    """Create a new property for the current user."""
    property_ = Property(
        user_id=current_user.id,
        address=data.address,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        county=data.county,
        property_type=data.property_type,
        num_units=data.num_units,
        bedrooms=data.bedrooms,
        bathrooms=data.bathrooms,
        square_footage=data.square_footage,
        lot_size=data.lot_size,
        year_built=data.year_built,
    )
    db.add(property_)
    await db.commit()
    await db.refresh(property_)
    return PropertyResponse.model_validate(property_)


@router.get("/", response_model=list[PropertyResponse])
async def list_properties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[PropertyResponse]:
    """List properties for the current user (paginated)."""
    result = await db.execute(
        select(Property)
        .where(Property.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    properties = result.scalars().all()
    return [PropertyResponse.model_validate(p) for p in properties]


@router.post("/lookup", response_model=PropertyLookupResponse)
async def lookup_property_data(
    data: PropertyLookupRequest,
    current_user: User = Depends(get_current_user),
) -> PropertyLookupResponse:
    """Lookup property/rent data from RentCast and return normalized form-prefill fields."""
    try:
        async with RentCastClient() as client:
            property_data = await client.lookup_property(data.address)
            rent_data = await client.get_rent_estimate(data.address)
    except PropertyNotFound:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "We couldn't find that property. Check the address and try again.",
                "error_code": "PROPERTY_NOT_FOUND",
            },
        )

    merged = {**property_data, **rent_data}
    if not merged.get("address"):
        merged["address"] = data.address

    return PropertyLookupResponse.model_validate(merged)


@router.get("/sample-data", response_model=PropertyLookupResponse)
async def get_sample_property_data() -> PropertyLookupResponse:
    """Return hardcoded sample lookup payload for demo mode without API calls."""
    return PropertyLookupResponse.model_validate(SAMPLE_LOOKUP_RESPONSE)


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    """Get a property by ID. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.user_id == current_user.id,
        )
    )
    property_ = result.scalar_one_or_none()
    if not property_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return PropertyResponse.model_validate(property_)


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: uuid.UUID,
    data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    """Update a property. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.user_id == current_user.id,
        )
    )
    property_ = result.scalar_one_or_none()
    if not property_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(property_, key, value)
    await db.commit()
    await db.refresh(property_)
    return PropertyResponse.model_validate(property_)


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a property. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.user_id == current_user.id,
        )
    )
    property_ = result.scalar_one_or_none()
    if not property_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    await db.delete(property_)
    await db.commit()
