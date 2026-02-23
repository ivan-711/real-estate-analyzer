"""
Risk scoring engine: 11 weighted factors, composite 0-100 score and label.

All factor scores are 0 (low risk) to 100 (high risk). Linear interpolation between thresholds.
"""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal


def _clamp(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    """Clamp value to [lo, hi] and quantize to 2 decimals."""
    q = Decimal("0.01")
    if value < lo:
        return lo.quantize(q, rounding=ROUND_HALF_UP)
    if value > hi:
        return hi.quantize(q, rounding=ROUND_HALF_UP)
    return value.quantize(q, rounding=ROUND_HALF_UP)


def _d(val: Decimal | float | None) -> Decimal:
    if val is None:
        return Decimal("0")
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


class RiskEngine:
    """Developer-owned risk scoring engine."""

    RISK_FACTORS: dict[str, dict[str, float | str]] = {
        "dscr_coverage": {
            "weight": 0.20,
            "description": "Debt Service Coverage Ratio",
        },
        "cash_on_cash": {
            "weight": 0.15,
            "description": "Cash-on-Cash Return",
        },
        "vacancy_vs_market": {
            "weight": 0.10,
            "description": "Vacancy Rate vs Market Average",
        },
        "ltv_ratio": {
            "weight": 0.10,
            "description": "Loan-to-Value Ratio",
        },
        "market_appreciation": {
            "weight": 0.10,
            "description": "Market Appreciation Trend",
        },
        "rent_to_price": {
            "weight": 0.10,
            "description": "Rent-to-Price Ratio",
        },
        "property_age": {
            "weight": 0.05,
            "description": "Property Age",
        },
        "days_on_market": {
            "weight": 0.05,
            "description": "Days on Market",
        },
        "population_growth": {
            "weight": 0.05,
            "description": "Population Growth",
        },
        "concentration_risk": {
            "weight": 0.05,
            "description": "Portfolio Concentration",
        },
        "expense_ratio": {
            "weight": 0.05,
            "description": "Operating Expense Ratio",
        },
    }

    @staticmethod
    def _score_dscr(dscr: Decimal) -> Decimal:
        """DSCR < 1.0 = 100 risk, DSCR >= 1.5 = 0 risk, linear between."""
        d = _d(dscr)
        if d >= Decimal("1.5"):
            return Decimal("0")
        if d <= Decimal("1.0"):
            return Decimal("100")
        # linear: 1.0 -> 100, 1.5 -> 0
        return _clamp(
            (Decimal("1.5") - d) / Decimal("0.5") * 100,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_cash_on_cash(coc: Decimal) -> Decimal:
        """CoC < 4% = 100 risk, CoC >= 10% = 0 risk, linear between."""
        c = _d(coc)
        if c >= Decimal("10"):
            return Decimal("0")
        if c <= Decimal("4"):
            return Decimal("100")
        return _clamp(
            (Decimal("10") - c) / Decimal("6") * 100,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_vacancy(deal_vacancy: Decimal, market_vacancy: Decimal) -> Decimal:
        """Above market vacancy = higher risk; below = lower. Linear around market."""
        d = _d(deal_vacancy)
        m = _d(market_vacancy)
        diff = d - m
        # diff > 0: above market -> risk up to 100; diff < 0: below -> risk down to 0
        # Map diff in [-10, 10] to [0, 100]: diff=10 -> 100, diff=-10 -> 0
        score = Decimal("50") + diff * Decimal("5")
        return _clamp(score, Decimal("0"), Decimal("100"))

    @staticmethod
    def _score_ltv(ltv: Decimal) -> Decimal:
        """LTV <= 80% = 0 risk, LTV >= 100% = 100 risk, linear 80-100."""
        ltv_pct = _d(ltv)
        if ltv_pct <= Decimal("80"):
            return Decimal("0")
        if ltv_pct >= Decimal("100"):
            return Decimal("100")
        return _clamp(
            (ltv_pct - Decimal("80")) / Decimal("20") * 100,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_market_appreciation(yoy_pct: Decimal) -> Decimal:
        """Declining YoY = higher risk. Negative -> high; positive -> low."""
        y = _d(yoy_pct)
        # y >= 5 -> 0, y <= -2 -> 100, linear
        if y >= Decimal("5"):
            return Decimal("0")
        if y <= Decimal("-2"):
            return Decimal("100")
        return _clamp(
            (Decimal("5") - y) / Decimal("7") * 100,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_rent_to_price(ratio: Decimal) -> Decimal:
        """ratio < 0.6% = 100 risk, ratio >= 1.0% = 0 risk. Ratio in percent."""
        r = _d(ratio)
        if r >= Decimal("1.0"):
            return Decimal("0")
        if r <= Decimal("0.6"):
            return Decimal("100")
        return _clamp(
            (Decimal("1.0") - r) / Decimal("0.4") * 100,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_property_age(year_built: int) -> Decimal:
        """Older than 50 years = higher risk. age = current_year - year_built."""
        if year_built is None:
            return Decimal("0")
        age = datetime.now().year - int(year_built)
        if age <= 0:
            return Decimal("0")
        if age >= 50:
            return _clamp(
                min(Decimal(age - 50) * 2 + Decimal("50"), Decimal("100")),
                Decimal("0"),
                Decimal("100"),
            )
        return _clamp(
            Decimal(age) / Decimal("50") * 50,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_days_on_market(days: int) -> Decimal:
        """<= 90 days = 0 risk; above 90 = increasing risk."""
        d = int(days) if days is not None else 0
        if d <= 90:
            return Decimal("0")
        # 90 -> 0, 180 -> 100 linear
        return _clamp(
            Decimal(d - 90) / Decimal("90") * 100,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_population_growth(growth_pct: Decimal) -> Decimal:
        """Declining = higher risk. Negative growth -> high score."""
        g = _d(growth_pct)
        if g >= Decimal("2"):
            return Decimal("0")
        if g <= Decimal("-1"):
            return Decimal("100")
        return _clamp(
            (Decimal("2") - g) / Decimal("3") * 100,
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_concentration(pct_in_zip: Decimal) -> Decimal:
        """> 50% in one ZIP = high risk."""
        p = _d(pct_in_zip)
        if p <= Decimal("50"):
            return Decimal("0")
        return _clamp(
            min((p - Decimal("50")) * 2, Decimal("100")),
            Decimal("0"),
            Decimal("100"),
        )

    @staticmethod
    def _score_expense_ratio(ratio: Decimal) -> Decimal:
        """Operating expenses > 55% of income = risk."""
        r = _d(ratio)
        if r <= Decimal("55"):
            return Decimal("0")
        return _clamp(
            min((r - Decimal("55")) * 2, Decimal("100")),
            Decimal("0"),
            Decimal("100"),
        )

    @classmethod
    def calculate_risk_score(
        cls,
        deal_metrics: dict,
        market_data: dict | None,
        portfolio_data: dict | None,
    ) -> dict:
        """
        Composite risk: weighted sum of factor scores; label Low/Moderate/High.
        Returns {"score": Decimal, "label": str, "factors": dict}.
        """
        dm = deal_metrics or {}
        md = market_data or {}
        pd = portfolio_data or {}

        purchase_price = _d(dm.get("purchase_price"))
        loan_amount = _d(dm.get("loan_amount"))
        gross_monthly_rent = _d(dm.get("gross_monthly_rent"))
        noi = _d(dm.get("noi"))
        vacancy_rate_pct = _d(dm.get("vacancy_rate_pct"))
        other_monthly_income = _d(dm.get("other_monthly_income"))

        ltv = (
            (loan_amount / purchase_price * 100)
            if purchase_price and purchase_price > 0
            else Decimal("0")
        )
        annual_rent = gross_monthly_rent * 12
        rent_to_price_pct = (
            (annual_rent / purchase_price * 100)
            if purchase_price and purchase_price > 0
            else Decimal("0")
        )
        egi_monthly = (
            gross_monthly_rent * (1 - vacancy_rate_pct / 100) + other_monthly_income
        )
        egi_annual = egi_monthly * 12
        expense_ratio_pct = (
            (100 * (1 - noi / egi_annual))
            if egi_annual and egi_annual > 0
            else Decimal("0")
        )

        dscr_val = dm.get("dscr")
        if dscr_val is not None:
            dscr_score = cls._score_dscr(_d(dscr_val))
        else:
            dscr_score = Decimal("0")

        coc_val = dm.get("cash_on_cash")
        if coc_val is not None:
            coc_score = cls._score_cash_on_cash(_d(coc_val))
        else:
            coc_score = Decimal("0")

        market_vacancy = _d(md.get("avg_vacancy_rate_pct", 5))
        vacancy_score = cls._score_vacancy(vacancy_rate_pct, market_vacancy)
        ltv_score = cls._score_ltv(ltv)
        yoy = _d(md.get("yoy_appreciation_pct", 0))
        market_appr_score = cls._score_market_appreciation(yoy)
        rent_to_price_score = cls._score_rent_to_price(rent_to_price_pct)

        year_built = dm.get("year_built")
        if year_built is not None:
            try:
                year_built = int(year_built)
            except (TypeError, ValueError):
                year_built = None
        property_age_score = cls._score_property_age(year_built or 0)

        days_on_market = dm.get("days_on_market")
        if days_on_market is not None:
            try:
                days_on_market = int(days_on_market)
            except (TypeError, ValueError):
                days_on_market = 0
        else:
            days_on_market = 0
        dom_score = cls._score_days_on_market(days_on_market)

        pop_growth = _d(pd.get("population_growth_pct", 0))
        pop_score = cls._score_population_growth(pop_growth)
        pct_zip = _d(pd.get("pct_in_zip", 0))
        conc_score = cls._score_concentration(pct_zip)
        exp_score = cls._score_expense_ratio(expense_ratio_pct)

        factors: dict[str, dict] = {
            "dscr_coverage": {"score": dscr_score, "raw": str(dm.get("dscr"))},
            "cash_on_cash": {"score": coc_score, "raw": str(dm.get("cash_on_cash"))},
            "vacancy_vs_market": {"score": vacancy_score},
            "ltv_ratio": {"score": ltv_score, "raw": str(ltv)},
            "market_appreciation": {"score": market_appr_score},
            "rent_to_price": {
                "score": rent_to_price_score,
                "raw": str(rent_to_price_pct),
            },
            "property_age": {"score": property_age_score},
            "days_on_market": {"score": dom_score},
            "population_growth": {"score": pop_score},
            "concentration_risk": {"score": conc_score},
            "expense_ratio": {"score": exp_score, "raw": str(expense_ratio_pct)},
        }

        total = Decimal("0")
        for key, info in cls.RISK_FACTORS.items():
            w = info["weight"]
            total += Decimal(str(w)) * factors[key]["score"]
        score = _clamp(total, Decimal("0"), Decimal("100"))

        if score <= Decimal("33"):
            label = "Low"
        elif score <= Decimal("66"):
            label = "Moderate"
        else:
            label = "High"

        return {
            "score": score,
            "label": label,
            "factors": factors,
        }
