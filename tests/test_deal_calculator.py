"""Tests for DealCalculator formulas."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.deal_calculator import DealCalculator

# PRD/CLAUDE example values:
# gross_rent=1800, vacancy=5%, tax=280, insurance=120,
# maintenance=5%, management=10%, HOA=0, utilities=0
# EGI: 1710, opex: 570, monthly NOI: 1140, annual NOI: 13680
EXAMPLE_INPUTS = {
    "purchase_price": Decimal("185000"),
    "down_payment_amount": Decimal("37000"),
    "loan_amount": Decimal("148000"),
    "interest_rate": Decimal("7.0"),
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
}

DEAL_INPUTS_FOR_CALCULATE_ALL = {
    "purchase_price": Decimal("185000"),
    "down_payment_pct": Decimal("20"),
    "loan_amount": Decimal("148000"),
    "interest_rate": Decimal("7.0"),
    "loan_term_years": 30,
    "closing_costs": Decimal("5550"),
    "rehab_costs": Decimal("0"),
    "gross_monthly_rent": Decimal("1800"),
    "other_monthly_income": Decimal("0"),
    "property_tax_monthly": Decimal("280"),
    "insurance_monthly": Decimal("120"),
    "vacancy_rate_pct": Decimal("5"),
    "maintenance_rate_pct": Decimal("5"),
    "management_fee_pct": Decimal("10"),
    "hoa_monthly": Decimal("0"),
    "utilities_monthly": Decimal("0"),
}


def test_calculate_noi() -> None:
    """NOI = (EGI - opex) * 12; with example inputs gives 12480."""
    result = DealCalculator.calculate_noi(
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
    # EGI 1710, opex 280+120+90+180 = 670, monthly NOI 1040, annual 12480
    assert result == Decimal("12480.00")


def test_calculate_cap_rate() -> None:
    """Cap rate = NOI / purchase price."""
    result = DealCalculator.calculate_cap_rate(
        noi=Decimal("13680"),
        purchase_price=EXAMPLE_INPUTS["purchase_price"],
    )
    assert result == Decimal("0.0739")  # 13680/185000


def test_zero_purchase_price_raises() -> None:
    """Cap rate must reject zero purchase price."""
    with pytest.raises(ValueError, match="positive"):
        DealCalculator.calculate_cap_rate(
            noi=Decimal("13680.00"),
            purchase_price=Decimal("0"),
        )


def test_calculate_cash_on_cash() -> None:
    """CoC = annual_cash_flow / total_cash_invested."""
    result = DealCalculator.calculate_cash_on_cash(
        annual_cash_flow=Decimal("4104"),
        total_cash_invested=Decimal("42550"),
    )
    assert result == Decimal("0.0965")  # 4104/42550 ≈ 9.65%


def test_calculate_dscr() -> None:
    """DSCR = NOI / annual debt service."""
    result = DealCalculator.calculate_dscr(
        noi=Decimal("13320"),
        annual_debt_service=Decimal("11820"),
    )
    assert result == Decimal("1.1269")  # 13320/11820, quantized 0.0001


def test_calculate_dscr_all_cash_returns_none() -> None:
    """Zero debt service (all-cash) returns None."""
    result = DealCalculator.calculate_dscr(
        noi=Decimal("13320"),
        annual_debt_service=Decimal("0"),
    )
    assert result is None


def test_calculate_grm() -> None:
    """GRM = purchase_price / annual_gross_rent."""
    result = DealCalculator.calculate_grm(
        purchase_price=EXAMPLE_INPUTS["purchase_price"],
        annual_gross_rent=Decimal("21600"),
    )
    assert result == Decimal("8.56")  # 185000/21600


def test_calculate_monthly_cash_flow() -> None:
    """Monthly cash flow = EGI - opex - mortgage."""
    result = DealCalculator.calculate_monthly_cash_flow(
        effective_gross_income_monthly=Decimal("1710"),
        operating_expenses_monthly=Decimal("570"),
        monthly_mortgage=EXAMPLE_INPUTS["monthly_mortgage_example"],
    )
    assert result == Decimal("155")  # 1710 - 570 - 985


def test_calculate_total_cash_invested() -> None:
    """Total cash invested = down + closing + rehab."""
    result = DealCalculator.calculate_total_cash_invested(
        purchase_price=EXAMPLE_INPUTS["purchase_price"],
        down_payment_amount=EXAMPLE_INPUTS["down_payment_amount"],
        closing_costs=EXAMPLE_INPUTS["closing_costs"],
        rehab_costs=Decimal("0"),
    )
    assert result == Decimal("42550")


def test_calculate_equity_buildup() -> None:
    """Equity buildup from principal paydown over 5 years."""
    result = DealCalculator.calculate_equity_buildup(
        loan_amount=EXAMPLE_INPUTS["loan_amount"],
        annual_rate=EXAMPLE_INPUTS["interest_rate_pct"],
        term_years=EXAMPLE_INPUTS["term_years"],
        years=5,
    )
    assert result > 0
    assert result < Decimal("148000")


def test_calculate_irr_projection() -> None:
    """IRR projection returns Decimal for 5-year hold."""
    inputs = dict(DEAL_INPUTS_FOR_CALCULATE_ALL)
    inputs["total_cash_invested"] = Decimal("42550")
    inputs["annual_cash_flow"] = Decimal("4104")
    result = DealCalculator.calculate_irr_projection(inputs, hold_years=5)
    assert isinstance(result, Decimal)


def test_calculate_all_returns_dict() -> None:
    """calculate_all returns dict with all expected keys and computed metrics."""
    result = DealCalculator.calculate_all(DEAL_INPUTS_FOR_CALCULATE_ALL)
    expected_keys = {
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
    }
    for key in expected_keys:
        assert key in result
    assert result["noi"] == Decimal("12480.00")
    assert result["total_cash_invested"] == Decimal("42550.00")
    assert result["grm"] == Decimal("8.56")
