"""Scaffold tests for DealCalculator formulas (developer-owned implementation pending)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.deal_calculator import DealCalculator

SKIP_REASON = "awaiting developer implementation"

# PRD example values (exact numbers requested):
# - Purchase: 185000
# - Down payment: 37000
# - Loan: 148000
# - Rate: 7.0%
# - Term: 30yr
# - Closing costs: 5550
# - Gross rent: 1800/mo
# - Vacancy: 5%
# - Property tax: 280/mo
# - Insurance: 120/mo
# - Maintenance: 5% of rent
# - Management: 10% of rent
# - HOA: 0
# - Utilities: 0
# - Mortgage (example): 985/mo
# - Net cash flow (example): 342/mo
EXAMPLE_INPUTS = {
    "purchase_price": Decimal("185000"),
    "down_payment_amount": Decimal("37000"),
    "loan_amount": Decimal("148000"),
    "interest_rate_pct": Decimal("7.0"),
    "term_years": 30,
    "closing_costs": Decimal("5550"),
    "gross_monthly_rent": Decimal("1800"),
    "vacancy_rate_pct": Decimal("5"),
    "property_tax_monthly": Decimal("280"),
    "insurance_monthly": Decimal("120"),
    "maintenance_rate_pct": Decimal("5"),
    "management_fee_pct": Decimal("10"),
    "hoa_monthly": Decimal("0"),
    "utilities_monthly": Decimal("0"),
    "monthly_mortgage_example": Decimal("985"),
    "monthly_cash_flow_example": Decimal("342"),
}


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_all_stub() -> None:
    """calculate_all should eventually orchestrate every individual metric formula."""
    # Expected output keys include: NOI, cap_rate, cash_on_cash, DSCR, GRM,
    # monthly/annual cash flow, total cash invested, 5yr/10yr IRR, equity buildup.
    DealCalculator.calculate_all({})


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_noi_stub() -> None:
    """NOI should use effective gross income minus operating expenses, annualized."""
    # Uses PRD example monthly inputs:
    # gross_rent=1800, vacancy=5%, tax=280, insurance=120,
    # maintenance=5% of rent, management=10% of rent, HOA=0, utilities=0.
    DealCalculator.calculate_noi(
        gross_monthly_rent=EXAMPLE_INPUTS["gross_monthly_rent"],
        vacancy_rate_pct=EXAMPLE_INPUTS["vacancy_rate_pct"],
        property_tax_monthly=EXAMPLE_INPUTS["property_tax_monthly"],
        insurance_monthly=EXAMPLE_INPUTS["insurance_monthly"],
        maintenance_rate_pct=EXAMPLE_INPUTS["maintenance_rate_pct"],
        management_fee_pct=EXAMPLE_INPUTS["management_fee_pct"],
        hoa_monthly=EXAMPLE_INPUTS["hoa_monthly"],
        utilities_monthly=EXAMPLE_INPUTS["utilities_monthly"],
        other_monthly_income=Decimal("0"),
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_cap_rate_stub() -> None:
    """Cap rate should compute NOI divided by purchase price."""
    # Purchase uses exact PRD example value: 185000.
    DealCalculator.calculate_cap_rate(
        noi=Decimal("0"),
        purchase_price=EXAMPLE_INPUTS["purchase_price"],
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_cash_on_cash_stub() -> None:
    """Cash-on-cash should compute annual cash flow divided by total cash invested."""
    # Total cash invested example components:
    # down payment=37000, closing costs=5550, rehab=0 (example placeholder).
    DealCalculator.calculate_cash_on_cash(
        annual_cash_flow=Decimal("0"),
        total_cash_invested=Decimal("42550"),
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_dscr_stub() -> None:
    """DSCR should compute NOI divided by annual debt service."""
    # Mortgage example is 985/mo, so annual debt service example is 11820.
    DealCalculator.calculate_dscr(
        noi=Decimal("0"),
        annual_debt_service=Decimal("11820"),
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_grm_stub() -> None:
    """GRM should compute purchase price divided by annual gross rent."""
    # Annual gross rent from exact PRD example monthly rent:
    # 1800 * 12 = 21600.
    DealCalculator.calculate_grm(
        purchase_price=EXAMPLE_INPUTS["purchase_price"],
        annual_gross_rent=Decimal("21600"),
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_monthly_cash_flow_stub() -> None:
    """Monthly cash flow should subtract operating expenses and mortgage from EGI."""
    # Net cash flow example should align with PRD example value: 342/mo.
    # Mortgage example should align with PRD example value: 985/mo.
    DealCalculator.calculate_monthly_cash_flow(
        effective_gross_income_monthly=Decimal("0"),
        operating_expenses_monthly=Decimal("0"),
        monthly_mortgage=EXAMPLE_INPUTS["monthly_mortgage_example"],
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_total_cash_invested_stub() -> None:
    """Total cash invested should include down payment + closing + rehab."""
    # Exact PRD values: purchase=185000, down payment=37000, closing=5550.
    DealCalculator.calculate_total_cash_invested(
        purchase_price=EXAMPLE_INPUTS["purchase_price"],
        down_payment_amount=EXAMPLE_INPUTS["down_payment_amount"],
        closing_costs=EXAMPLE_INPUTS["closing_costs"],
        rehab_costs=Decimal("0"),
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_equity_buildup_stub() -> None:
    """Equity buildup should come from principal paydown over time."""
    # Exact PRD financing inputs:
    # loan=148000, rate=7.0%, term=30 years.
    DealCalculator.calculate_equity_buildup(
        loan_amount=EXAMPLE_INPUTS["loan_amount"],
        annual_rate=EXAMPLE_INPUTS["interest_rate_pct"],
        term_years=EXAMPLE_INPUTS["term_years"],
        years=5,
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_irr_projection_stub() -> None:
    """IRR projection should use hold-period cash flows plus exit proceeds."""
    # Use exact PRD example purchase/rent/expense inputs above for 5-year hold.
    DealCalculator.calculate_irr_projection(
        deal_inputs=dict(EXAMPLE_INPUTS),
        hold_years=5,
    )
