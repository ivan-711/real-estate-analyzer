from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DealPreviewRequest(BaseModel):
    """Request for guest deal preview (no auth, no property_id). Same financial inputs as DealCreate."""

    deal_name: Optional[str] = Field(None, max_length=100)
    purchase_price: Decimal = Field(..., gt=0)
    closing_costs: Optional[Decimal] = Field(None, ge=0)
    rehab_costs: Optional[Decimal] = Field(None, ge=0)
    after_repair_value: Optional[Decimal] = Field(None, gt=0)
    down_payment_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    loan_amount: Optional[Decimal] = Field(None, ge=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=30)
    loan_term_years: Optional[int] = Field(None, ge=1, le=50)
    monthly_mortgage: Optional[Decimal] = Field(None, ge=0)
    gross_monthly_rent: Decimal = Field(..., ge=0)
    other_monthly_income: Optional[Decimal] = Field(None, ge=0)
    property_tax_monthly: Optional[Decimal] = Field(None, ge=0)
    insurance_monthly: Optional[Decimal] = Field(None, ge=0)
    vacancy_rate_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    maintenance_rate_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    management_fee_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    hoa_monthly: Optional[Decimal] = Field(None, ge=0)
    utilities_monthly: Optional[Decimal] = Field(None, ge=0)


class DealPreviewResponse(BaseModel):
    """Preview response: all computed metrics and risk, no DB fields."""

    purchase_price: Decimal
    gross_monthly_rent: Decimal
    down_payment_pct: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    loan_term_years: Optional[int] = None
    closing_costs: Optional[Decimal] = None
    rehab_costs: Optional[Decimal] = None
    property_tax_monthly: Optional[Decimal] = None
    insurance_monthly: Optional[Decimal] = None
    vacancy_rate_pct: Optional[Decimal] = None
    maintenance_rate_pct: Optional[Decimal] = None
    management_fee_pct: Optional[Decimal] = None
    noi: Optional[Decimal] = None
    cap_rate: Optional[Decimal] = None
    cash_on_cash: Optional[Decimal] = None
    monthly_cash_flow: Optional[Decimal] = None
    annual_cash_flow: Optional[Decimal] = None
    total_cash_invested: Optional[Decimal] = None
    dscr: Optional[Decimal] = None
    grm: Optional[Decimal] = None
    irr_5yr: Optional[Decimal] = None
    irr_10yr: Optional[Decimal] = None
    equity_buildup_5yr: Optional[Decimal] = None
    equity_buildup_10yr: Optional[Decimal] = None
    risk_score: Optional[Decimal] = None
    risk_factors: Optional[dict] = None
    loan_amount: Optional[Decimal] = None
    monthly_mortgage: Optional[Decimal] = None


class DealCreate(BaseModel):
    """Fields for creating a deal (inputs only; calculated fields left None)."""

    property_id: uuid.UUID
    deal_name: Optional[str] = Field(None, max_length=100)
    purchase_price: Decimal = Field(..., gt=0)
    closing_costs: Optional[Decimal] = Field(None, ge=0)
    rehab_costs: Optional[Decimal] = Field(None, ge=0)
    after_repair_value: Optional[Decimal] = Field(None, gt=0)
    down_payment_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    loan_amount: Optional[Decimal] = Field(None, ge=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=30)
    loan_term_years: Optional[int] = Field(None, ge=1, le=50)
    monthly_mortgage: Optional[Decimal] = Field(None, ge=0)
    gross_monthly_rent: Decimal = Field(..., ge=0)
    other_monthly_income: Optional[Decimal] = Field(None, ge=0)
    property_tax_monthly: Optional[Decimal] = Field(None, ge=0)
    insurance_monthly: Optional[Decimal] = Field(None, ge=0)
    vacancy_rate_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    maintenance_rate_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    management_fee_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    hoa_monthly: Optional[Decimal] = Field(None, ge=0)
    utilities_monthly: Optional[Decimal] = Field(None, ge=0)


class DealUpdate(BaseModel):
    """All fields optional for partial updates."""

    deal_name: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)
    purchase_price: Optional[Decimal] = Field(None, gt=0)
    closing_costs: Optional[Decimal] = Field(None, ge=0)
    rehab_costs: Optional[Decimal] = Field(None, ge=0)
    after_repair_value: Optional[Decimal] = Field(None, gt=0)
    down_payment_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    loan_amount: Optional[Decimal] = Field(None, ge=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=30)
    loan_term_years: Optional[int] = Field(None, ge=1, le=50)
    monthly_mortgage: Optional[Decimal] = Field(None, ge=0)
    gross_monthly_rent: Optional[Decimal] = Field(None, ge=0)
    other_monthly_income: Optional[Decimal] = Field(None, ge=0)
    property_tax_monthly: Optional[Decimal] = Field(None, ge=0)
    insurance_monthly: Optional[Decimal] = Field(None, ge=0)
    vacancy_rate_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    maintenance_rate_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    management_fee_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    hoa_monthly: Optional[Decimal] = Field(None, ge=0)
    utilities_monthly: Optional[Decimal] = Field(None, ge=0)


class DealSummaryResponse(BaseModel):
    """Portfolio KPI summary for the current user's deals."""

    model_config = ConfigDict(from_attributes=True)

    total_monthly_cash_flow: Decimal
    average_cap_rate: Optional[Decimal] = None
    average_cash_on_cash: Optional[Decimal] = None
    total_equity: Decimal
    active_deal_count: int
    average_risk_score: Optional[Decimal] = None


class DealResponse(BaseModel):
    """Deal as returned by API (includes all input and calculated fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    user_id: uuid.UUID
    deal_name: Optional[str]
    status: str
    purchase_price: Decimal
    closing_costs: Optional[Decimal]
    rehab_costs: Optional[Decimal]
    after_repair_value: Optional[Decimal]
    down_payment_pct: Optional[Decimal]
    loan_amount: Optional[Decimal]
    interest_rate: Optional[Decimal]
    loan_term_years: Optional[int]
    monthly_mortgage: Optional[Decimal]
    gross_monthly_rent: Decimal
    other_monthly_income: Optional[Decimal]
    property_tax_monthly: Optional[Decimal]
    insurance_monthly: Optional[Decimal]
    vacancy_rate_pct: Optional[Decimal]
    maintenance_rate_pct: Optional[Decimal]
    management_fee_pct: Optional[Decimal]
    hoa_monthly: Optional[Decimal]
    utilities_monthly: Optional[Decimal]
    noi: Optional[Decimal]
    cap_rate: Optional[Decimal]
    cash_on_cash: Optional[Decimal]
    monthly_cash_flow: Optional[Decimal]
    annual_cash_flow: Optional[Decimal]
    total_cash_invested: Optional[Decimal]
    dscr: Optional[Decimal]
    grm: Optional[Decimal]
    irr_5yr: Optional[Decimal]
    irr_10yr: Optional[Decimal]
    equity_buildup_5yr: Optional[Decimal]
    equity_buildup_10yr: Optional[Decimal]
    risk_score: Optional[Decimal]
    risk_factors: Optional[dict]
    created_at: datetime
    updated_at: datetime
    property_address: Optional[str] = None
    property_city: Optional[str] = None
    property_state: Optional[str] = None


class YearlyProjection(BaseModel):
    year: int
    property_value: Decimal
    loan_balance: Decimal
    equity: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    annual_gross_rent: Decimal
    annual_expenses: Decimal
    annual_mortgage_payment: Decimal
    annual_net_cash_flow: Decimal
    cumulative_cash_flow: Decimal


class ProjectionParameters(BaseModel):
    projection_years: int
    annual_appreciation_pct: Decimal
    annual_rent_growth_pct: Decimal
    annual_expense_growth_pct: Decimal
    selling_cost_pct: Decimal


class DealProjectionsResponse(BaseModel):
    deal_id: uuid.UUID
    deal_name: Optional[str]
    parameters: ProjectionParameters
    irr_5_year: Optional[Decimal]
    irr_10_year: Optional[Decimal]
    yearly_projections: list[YearlyProjection]
