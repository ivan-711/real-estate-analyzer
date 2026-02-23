"""Tests for RiskEngine factor scoring."""

from __future__ import annotations

from decimal import Decimal

from app.services.risk_engine import RiskEngine

# Sheboygan duplex example (architecture docs): risk ~28 (Low)
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


def test_calculate_risk_score_returns_shape() -> None:
    """Composite risk score returns score, label, and factors."""
    result = RiskEngine.calculate_risk_score(
        deal_metrics=dict(SHEBOYGAN_DEAL_METRICS),
        market_data=dict(SHEBOYGAN_MARKET_DATA),
        portfolio_data=dict(SHEBOYGAN_PORTFOLIO_DATA),
    )
    assert "score" in result
    assert "label" in result
    assert "factors" in result
    assert Decimal("0") <= result["score"] <= Decimal("100")
    assert result["label"] in ("Low", "Moderate", "High")
    assert result["score"] <= Decimal("33")  # Sheboygan example is Low (~28)


def test_score_dscr_boundary_exactly_1_0() -> None:
    """DSCR 1.0 is high risk boundary -> 100."""
    result = RiskEngine._score_dscr(Decimal("1.0"))
    assert result == Decimal("100")


def test_score_dscr_boundary_exactly_1_5() -> None:
    """DSCR >= 1.5 is low risk -> 0."""
    result = RiskEngine._score_dscr(Decimal("1.5"))
    assert result == Decimal("0")


def test_score_cash_on_cash_boundary_exactly_4_pct() -> None:
    """CoC <= 4% is high risk -> 100."""
    result = RiskEngine._score_cash_on_cash(Decimal("4"))
    assert result == Decimal("100")


def test_score_cash_on_cash_boundary_exactly_10_pct() -> None:
    """CoC >= 10% is low risk -> 0."""
    result = RiskEngine._score_cash_on_cash(Decimal("10"))
    assert result == Decimal("0")


def test_score_vacancy() -> None:
    """Vacancy score is 0-100."""
    result = RiskEngine._score_vacancy(
        deal_vacancy=SHEBOYGAN_DEAL_METRICS["vacancy_rate_pct"],
        market_vacancy=SHEBOYGAN_MARKET_DATA["avg_vacancy_rate_pct"],
    )
    assert isinstance(result, Decimal)
    assert Decimal("0") <= result <= Decimal("100")


def test_score_ltv() -> None:
    """LTV <= 80% -> 0 risk."""
    result = RiskEngine._score_ltv(Decimal("80"))
    assert result == Decimal("0")


def test_score_market_appreciation() -> None:
    """Market appreciation score is 0-100."""
    result = RiskEngine._score_market_appreciation(
        yoy_pct=SHEBOYGAN_MARKET_DATA["yoy_appreciation_pct"]
    )
    assert isinstance(result, Decimal)
    assert Decimal("0") <= result <= Decimal("100")


def test_score_rent_to_price() -> None:
    """Rent-to-price 0.97% is between 0.6 and 1.0 -> score in (0, 100)."""
    result = RiskEngine._score_rent_to_price(
        ratio=SHEBOYGAN_DEAL_METRICS["rent_to_price_ratio_pct"]
    )
    assert isinstance(result, Decimal)
    assert Decimal("0") <= result <= Decimal("100")


def test_score_property_age() -> None:
    """Property age score is 0-100."""
    result = RiskEngine._score_property_age(
        year_built=SHEBOYGAN_DEAL_METRICS["year_built"]
    )
    assert isinstance(result, Decimal)
    assert Decimal("0") <= result <= Decimal("100")


def test_score_days_on_market() -> None:
    """45 days <= 90 -> 0 risk."""
    result = RiskEngine._score_days_on_market(
        days=SHEBOYGAN_DEAL_METRICS["days_on_market"]
    )
    assert result == Decimal("0")


def test_score_population_growth() -> None:
    """Population growth score is 0-100."""
    result = RiskEngine._score_population_growth(
        growth_pct=SHEBOYGAN_MARKET_DATA["population_growth_pct"]
    )
    assert isinstance(result, Decimal)
    assert Decimal("0") <= result <= Decimal("100")


def test_score_concentration() -> None:
    """35% <= 50% -> 0 risk."""
    result = RiskEngine._score_concentration(
        pct_in_zip=SHEBOYGAN_PORTFOLIO_DATA["pct_in_zip"]
    )
    assert result == Decimal("0")


def test_score_expense_ratio() -> None:
    """43% <= 55% -> 0 risk."""
    result = RiskEngine._score_expense_ratio(
        ratio=SHEBOYGAN_DEAL_METRICS["expense_ratio_pct"]
    )
    assert result == Decimal("0")
