from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Optional

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.deal import Deal
from app.models.property import Property
from app.models.user import User
from app.schemas.deal import (
    DealCreate,
    DealPreviewRequest,
    DealPreviewResponse,
    DealResponse,
    DealUpdate,
)
from app.services.deal_calculator import DealCalculator
from app.services.risk_engine import RiskEngine
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/deals", tags=["deals"])

DEAL_INPUT_FIELDS = (
    "property_id",
    "deal_name",
    "purchase_price",
    "closing_costs",
    "rehab_costs",
    "after_repair_value",
    "down_payment_pct",
    "loan_amount",
    "interest_rate",
    "loan_term_years",
    "monthly_mortgage",
    "gross_monthly_rent",
    "other_monthly_income",
    "property_tax_monthly",
    "insurance_monthly",
    "vacancy_rate_pct",
    "maintenance_rate_pct",
    "management_fee_pct",
    "hoa_monthly",
    "utilities_monthly",
)

CALCULATED_METRIC_FIELDS = (
    "noi",
    "cap_rate",
    "cash_on_cash",
    "monthly_cash_flow",
    "annual_cash_flow",
    "total_cash_invested",
    "dscr",
    "grm",
    "irr_5yr",
    "irr_10yr",
    "equity_buildup_5yr",
    "equity_buildup_10yr",
)


def _apply_calculated_metrics(deal: Deal, metrics: dict) -> None:
    """Apply available calculated metrics to the deal model instance."""
    for field in CALCULATED_METRIC_FIELDS:
        if field in metrics:
            setattr(deal, field, metrics[field])


def _build_deal_inputs_payload(deal: Deal) -> dict:
    """Build calculator/risk input payload from deal model fields."""
    return {field: getattr(deal, field) for field in DEAL_INPUT_FIELDS}


def _json_safe(obj: Any) -> Any:
    """Convert Decimals and nested dicts to JSON-serializable form for JSONB."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def _apply_risk_result(deal: Deal, risk_result: dict) -> None:
    """Apply available risk engine outputs to the deal model instance."""
    if "score" in risk_result:
        deal.risk_score = risk_result["score"]
    if "factors" in risk_result:
        deal.risk_factors = _json_safe(risk_result["factors"])


def _build_inputs_from_data(data: DealCreate | DealPreviewRequest) -> dict:
    """Build calculator/risk input payload from create or preview request."""
    return {
        "property_id": getattr(data, "property_id", None),
        "deal_name": data.deal_name,
        "purchase_price": data.purchase_price,
        "closing_costs": data.closing_costs,
        "rehab_costs": data.rehab_costs,
        "after_repair_value": data.after_repair_value,
        "down_payment_pct": data.down_payment_pct,
        "loan_amount": data.loan_amount,
        "interest_rate": data.interest_rate,
        "loan_term_years": data.loan_term_years,
        "monthly_mortgage": data.monthly_mortgage,
        "gross_monthly_rent": data.gross_monthly_rent,
        "other_monthly_income": data.other_monthly_income,
        "property_tax_monthly": data.property_tax_monthly,
        "insurance_monthly": data.insurance_monthly,
        "vacancy_rate_pct": data.vacancy_rate_pct,
        "maintenance_rate_pct": data.maintenance_rate_pct,
        "management_fee_pct": data.management_fee_pct,
        "hoa_monthly": data.hoa_monthly,
        "utilities_monthly": data.utilities_monthly,
    }


@router.post("/preview", response_model=DealPreviewResponse)
async def preview_deal(data: DealPreviewRequest) -> DealPreviewResponse:
    """Preview deal metrics without saving. No auth required. For guest analysis."""
    deal_inputs = _build_inputs_from_data(data)
    try:
        calculated_metrics = DealCalculator.calculate_all(deal_inputs)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": str(e),
                "error_code": "INVALID_DEAL_INPUTS",
            },
        ) from e

    risk_inputs = dict(deal_inputs)
    if calculated_metrics:
        risk_inputs.update(calculated_metrics)
    risk_score: Optional[Decimal] = None
    risk_factors: Optional[dict] = None
    try:
        risk_result = RiskEngine.calculate_risk_score(
            deal_metrics=risk_inputs,
            market_data=None,
            portfolio_data=None,
        )
        if risk_result:
            risk_score = risk_result.get("score")
            risk_factors = _json_safe(risk_result.get("factors", {}))
    except Exception:
        pass

    metrics = calculated_metrics or {}
    return DealPreviewResponse(
        purchase_price=data.purchase_price,
        gross_monthly_rent=data.gross_monthly_rent,
        down_payment_pct=data.down_payment_pct,
        interest_rate=data.interest_rate,
        loan_term_years=data.loan_term_years,
        closing_costs=data.closing_costs,
        rehab_costs=data.rehab_costs,
        property_tax_monthly=data.property_tax_monthly,
        insurance_monthly=data.insurance_monthly,
        vacancy_rate_pct=data.vacancy_rate_pct,
        maintenance_rate_pct=data.maintenance_rate_pct,
        management_fee_pct=data.management_fee_pct,
        noi=metrics.get("noi"),
        cap_rate=metrics.get("cap_rate"),
        cash_on_cash=metrics.get("cash_on_cash"),
        monthly_cash_flow=metrics.get("monthly_cash_flow"),
        annual_cash_flow=metrics.get("annual_cash_flow"),
        total_cash_invested=metrics.get("total_cash_invested"),
        dscr=metrics.get("dscr"),
        grm=metrics.get("grm"),
        irr_5yr=metrics.get("irr_5yr"),
        irr_10yr=metrics.get("irr_10yr"),
        equity_buildup_5yr=metrics.get("equity_buildup_5yr"),
        equity_buildup_10yr=metrics.get("equity_buildup_10yr"),
        risk_score=risk_score,
        risk_factors=risk_factors,
        loan_amount=metrics.get("loan_amount") or risk_inputs.get("loan_amount"),
        monthly_mortgage=metrics.get("monthly_mortgage")
        or risk_inputs.get("monthly_mortgage"),
    )


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

    deal_inputs = _build_deal_inputs_payload(deal)
    try:
        calculated_metrics = DealCalculator.calculate_all(deal_inputs)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": str(e),
                "error_code": "INVALID_DEAL_INPUTS",
            },
        ) from e
    if calculated_metrics:
        _apply_calculated_metrics(deal, calculated_metrics)

    risk_inputs = dict(deal_inputs)
    if calculated_metrics:
        risk_inputs.update(calculated_metrics)
    try:
        risk_result = RiskEngine.calculate_risk_score(
            deal_metrics=risk_inputs,
            market_data=None,
            portfolio_data=None,
        )
        if risk_result:
            _apply_risk_result(deal, risk_result)
    except Exception:
        deal.risk_score = None
        deal.risk_factors = None

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
    deal_inputs = _build_deal_inputs_payload(deal)
    try:
        calculated_metrics = DealCalculator.calculate_all(deal_inputs)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": str(e),
                "error_code": "INVALID_DEAL_INPUTS",
            },
        ) from e
    if calculated_metrics:
        _apply_calculated_metrics(deal, calculated_metrics)
    risk_inputs = dict(deal_inputs)
    if calculated_metrics:
        risk_inputs.update(calculated_metrics)
    try:
        risk_result = RiskEngine.calculate_risk_score(
            deal_metrics=risk_inputs,
            market_data=None,
            portfolio_data=None,
        )
        if risk_result:
            _apply_risk_result(deal, risk_result)
    except Exception:
        deal.risk_score = None
        deal.risk_factors = None
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
