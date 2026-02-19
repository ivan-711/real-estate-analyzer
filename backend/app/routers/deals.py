from __future__ import annotations

import uuid
from typing import Optional

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.deal import Deal
from app.models.property import Property
from app.models.user import User
from app.schemas.deal import DealCreate, DealResponse, DealUpdate
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/deals", tags=["deals"])


@router.post("/", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    data: DealCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealResponse:
    """Create a new deal for a property. Property must belong to current user."""
    prop_result = await db.execute(
        select(Property).where(
            Property.id == data.property_id,
            Property.user_id == current_user.id,
        )
    )
    property_ = prop_result.scalar_one_or_none()
    if not property_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    deal = Deal(
        property_id=data.property_id,
        user_id=current_user.id,
        deal_name=data.deal_name,
        purchase_price=data.purchase_price,
        closing_costs=data.closing_costs,
        rehab_costs=data.rehab_costs,
        after_repair_value=data.after_repair_value,
        down_payment_pct=data.down_payment_pct,
        loan_amount=data.loan_amount,
        interest_rate=data.interest_rate,
        loan_term_years=data.loan_term_years,
        monthly_mortgage=data.monthly_mortgage,
        gross_monthly_rent=data.gross_monthly_rent,
        other_monthly_income=data.other_monthly_income,
        property_tax_monthly=data.property_tax_monthly,
        insurance_monthly=data.insurance_monthly,
        vacancy_rate_pct=data.vacancy_rate_pct,
        maintenance_rate_pct=data.maintenance_rate_pct,
        management_fee_pct=data.management_fee_pct,
        hoa_monthly=data.hoa_monthly,
        utilities_monthly=data.utilities_monthly,
    )
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return DealResponse.model_validate(deal)


@router.get("/", response_model=list[DealResponse])
async def list_deals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    property_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[DealResponse]:
    """List deals for the current user (filterable by status, property_id)."""
    stmt = select(Deal).where(Deal.user_id == current_user.id)
    if status_filter is not None:
        stmt = stmt.where(Deal.status == status_filter)
    if property_id is not None:
        stmt = stmt.where(Deal.property_id == property_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    deals = result.scalars().all()
    return [DealResponse.model_validate(d) for d in deals]


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealResponse:
    """Get a deal by ID. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    return DealResponse.model_validate(deal)


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: uuid.UUID,
    data: DealUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealResponse:
    """Update a deal. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(deal, key, value)
    await db.commit()
    await db.refresh(deal)
    return DealResponse.model_validate(deal)


@router.delete(
    "/{deal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_deal(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a deal. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    await db.delete(deal)
    await db.commit()
