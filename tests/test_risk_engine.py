"""Scaffold tests for RiskEngine factor scoring (developer-owned implementation pending)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.risk_engine import RiskEngine

SKIP_REASON = "awaiting developer implementation"

# Sheboygan duplex example values from architecture docs:
# - Address: 123 Elm St, Sheboygan WI 53081
# - Purchase: 185000
# - Loan: 148000 @ 7.0%
# - Rent: 1800/mo
# - Vacancy: 5%
# - NOI: 13320
# - CoC: 11.1%
# - DSCR: 1.45
# - GRM: 8.6
# - Risk (example narrative): 28/100 (Low)
SHEBOYGAN_DEAL_METRICS = {
    "purchase_price": Decimal("185000"),
    "loan_amount": Decimal("148000"),
    "gross_monthly_rent": Decimal("1800"),
    "vacancy_rate_pct": Decimal("5"),
    "noi": Decimal("13320"),
    "cash_on_cash": Decimal("11.1"),
    "dscr": Decimal("1.45"),
    "grm": Decimal("8.6"),
    "rent_to_price_ratio_pct": Decimal("0.97"),
    "year_built": 1965,
    "days_on_market": 45,
    "expense_ratio_pct": Decimal("43"),
}

SHEBOYGAN_MARKET_DATA = {
    "avg_vacancy_rate_pct": Decimal("5"),
    "yoy_appreciation_pct": Decimal("3.2"),
    "population_growth_pct": Decimal("0.8"),
}

SHEBOYGAN_PORTFOLIO_DATA = {
    "pct_in_zip": Decimal("35"),
}


@pytest.mark.skip(reason=SKIP_REASON)
def test_calculate_risk_score_stub() -> None:
    """Composite risk score should return score, label, and weighted factor breakdown."""
    RiskEngine.calculate_risk_score(
        deal_metrics=dict(SHEBOYGAN_DEAL_METRICS),
        market_data=dict(SHEBOYGAN_MARKET_DATA),
        portfolio_data=dict(SHEBOYGAN_PORTFOLIO_DATA),
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_dscr_boundary_exactly_1_0() -> None:
    """DSCR exactly 1.0 should map to boundary behavior per architecture criteria."""
    # Boundary from architecture: DSCR < 1.0 high risk, > 1.5 low risk.
    RiskEngine._score_dscr(Decimal("1.0"))


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_dscr_boundary_exactly_1_5() -> None:
    """DSCR exactly 1.5 should map to boundary behavior per architecture criteria."""
    # Boundary from architecture: DSCR < 1.0 high risk, > 1.5 low risk.
    RiskEngine._score_dscr(Decimal("1.5"))


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_cash_on_cash_boundary_exactly_4_pct() -> None:
    """CoC exactly 4% should map to boundary behavior per architecture criteria."""
    # Boundary from architecture: CoC < 4% high risk, > 10% low risk.
    RiskEngine._score_cash_on_cash(Decimal("4"))


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_cash_on_cash_boundary_exactly_10_pct() -> None:
    """CoC exactly 10% should map to boundary behavior per architecture criteria."""
    # Boundary from architecture: CoC < 4% high risk, > 10% low risk.
    RiskEngine._score_cash_on_cash(Decimal("10"))


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_vacancy_stub() -> None:
    """Vacancy scoring should compare deal vacancy to market average vacancy."""
    RiskEngine._score_vacancy(
        deal_vacancy=SHEBOYGAN_DEAL_METRICS["vacancy_rate_pct"],
        market_vacancy=SHEBOYGAN_MARKET_DATA["avg_vacancy_rate_pct"],
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_ltv_stub() -> None:
    """LTV scoring should penalize higher leverage (above ~80%)."""
    RiskEngine._score_ltv(Decimal("80"))


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_market_appreciation_stub() -> None:
    """Market appreciation scoring should penalize declining trend conditions."""
    RiskEngine._score_market_appreciation(
        yoy_pct=SHEBOYGAN_MARKET_DATA["yoy_appreciation_pct"]
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_rent_to_price_stub() -> None:
    """Rent-to-price scoring should use architecture thresholds around 0.6%-1.0%."""
    RiskEngine._score_rent_to_price(
        ratio=SHEBOYGAN_DEAL_METRICS["rent_to_price_ratio_pct"]
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_property_age_stub() -> None:
    """Property age scoring should penalize properties older than 50 years."""
    RiskEngine._score_property_age(year_built=SHEBOYGAN_DEAL_METRICS["year_built"])


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_days_on_market_stub() -> None:
    """Days-on-market scoring should penalize listings above 90 days."""
    RiskEngine._score_days_on_market(days=SHEBOYGAN_DEAL_METRICS["days_on_market"])


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_population_growth_stub() -> None:
    """Population growth scoring should penalize declining demand demographics."""
    RiskEngine._score_population_growth(
        growth_pct=SHEBOYGAN_MARKET_DATA["population_growth_pct"]
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_concentration_stub() -> None:
    """Concentration scoring should penalize portfolios over 50% in one ZIP."""
    RiskEngine._score_concentration(
        pct_in_zip=SHEBOYGAN_PORTFOLIO_DATA["pct_in_zip"]
    )


@pytest.mark.skip(reason=SKIP_REASON)
def test_score_expense_ratio_stub() -> None:
    """Expense ratio scoring should penalize operating expenses above 55% of income."""
    RiskEngine._score_expense_ratio(ratio=SHEBOYGAN_DEAL_METRICS["expense_ratio_pct"])
