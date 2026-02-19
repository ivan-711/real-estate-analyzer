from __future__ import annotations

from decimal import Decimal


class RiskEngine:
    """Developer-owned risk scoring engine scaffold."""

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

    @classmethod
    def calculate_risk_score(
        cls,
        deal_metrics: dict,
        market_data: dict | None,
        portfolio_data: dict | None,
    ) -> dict:
        """
        Return composite risk result for a deal.

        Intended output shape:
        {
            "score": Decimal,   # 0-100, lower is safer
            "label": str,       # e.g., Low/Moderate/High
            "factors": dict,    # weighted + raw factor breakdown
        }
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_dscr(dscr: Decimal) -> Decimal:
        """
        Score DSCR risk.

        Criteria: DSCR < 1.0 = 100 risk, DSCR > 1.5 = 0 risk, linear between.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_cash_on_cash(coc: Decimal) -> Decimal:
        """
        Score cash-on-cash risk.

        Criteria: CoC < 4% = 100 risk, CoC > 10% = 0 risk, linear between.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_vacancy(deal_vacancy: Decimal, market_vacancy: Decimal) -> Decimal:
        """
        Score vacancy-vs-market risk.

        Criteria: vacancy above market average increases risk; below market lowers risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_ltv(ltv: Decimal) -> Decimal:
        """
        Score loan-to-value risk.

        Criteria: LTV above 80% implies higher financing risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_market_appreciation(yoy_pct: Decimal) -> Decimal:
        """
        Score market appreciation trend risk.

        Criteria: declining year-over-year appreciation indicates higher market risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_rent_to_price(ratio: Decimal) -> Decimal:
        """
        Score rent-to-price ratio risk.

        Criteria: ratio < 0.6% = 100 risk, ratio > 1.0% = 0 risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_property_age(year_built: int) -> Decimal:
        """
        Score property age risk.

        Criteria: properties older than 50 years carry higher maintenance risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_days_on_market(days: int) -> Decimal:
        """
        Score liquidity risk from days on market.

        Criteria: listings above 90 days indicate elevated liquidity risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_population_growth(growth_pct: Decimal) -> Decimal:
        """
        Score population growth risk.

        Criteria: declining population growth indicates demand-side risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_concentration(pct_in_zip: Decimal) -> Decimal:
        """
        Score portfolio concentration risk.

        Criteria: more than 50% of portfolio in one ZIP implies high concentration risk.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def _score_expense_ratio(ratio: Decimal) -> Decimal:
        """
        Score operating expense ratio risk.

        Criteria: operating expenses above 55% of income indicate elevated risk.
        """
        raise NotImplementedError("Developer will implement")
