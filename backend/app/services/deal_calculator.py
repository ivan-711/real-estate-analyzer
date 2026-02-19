from __future__ import annotations

from decimal import Decimal


class DealCalculator:
    """Developer-owned financial calculator service for deal metrics."""

    @staticmethod
    def calculate_all(deal_inputs: dict) -> dict:
        """
        Calculate and return all derived deal metrics from raw deal inputs.

        Intended orchestration (per architecture/domain docs):
        1. Compute total cash invested and financing details.
        2. Compute vacancy loss and effective gross income.
        3. Compute operating expenses (excluding debt service).
        4. Compute annual NOI and cash-flow metrics.
        5. Compute cap rate, cash-on-cash, DSCR, and GRM.
        6. Compute projection metrics (IRR and equity buildup).

        The output dict should contain calculated model fields such as:
        monthly_cash_flow, annual_cash_flow, noi, cap_rate, cash_on_cash,
        dscr, grm, irr_5yr, irr_10yr, equity_buildup_5yr, equity_buildup_10yr.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_noi(
        gross_monthly_rent: Decimal,
        vacancy_rate_pct: Decimal,
        property_tax_monthly: Decimal,
        insurance_monthly: Decimal,
        maintenance_rate_pct: Decimal,
        management_fee_pct: Decimal,
        hoa_monthly: Decimal,
        utilities_monthly: Decimal,
        other_monthly_income: Decimal,
    ) -> Decimal:
        """
        Calculate annual Net Operating Income (NOI).

        Intended formula:
        - Vacancy loss (monthly) = gross_monthly_rent * vacancy_rate_pct / 100
        - Effective gross income (monthly) =
          gross_monthly_rent + other_monthly_income - vacancy_loss
        - Maintenance (monthly) = gross_monthly_rent * maintenance_rate_pct / 100
        - Management (monthly) = gross_monthly_rent * management_fee_pct / 100
        - Total operating expenses (monthly) =
          property_tax_monthly + insurance_monthly + maintenance +
          management + hoa_monthly + utilities_monthly
        - NOI (annual) = (effective gross income - operating expenses) * 12

        Mortgage/debt service is explicitly excluded from NOI.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_cap_rate(noi: Decimal, purchase_price: Decimal) -> Decimal:
        """
        Calculate capitalization rate.

        Intended formula:
        cap_rate = noi / purchase_price
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_cash_on_cash(
        annual_cash_flow: Decimal,
        total_cash_invested: Decimal,
    ) -> Decimal:
        """
        Calculate cash-on-cash return.

        Intended formula:
        cash_on_cash = annual_cash_flow / total_cash_invested

        Where annual_cash_flow is post-debt-service cash flow and
        total_cash_invested reflects cash actually deployed.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_dscr(noi: Decimal, annual_debt_service: Decimal) -> Decimal:
        """
        Calculate Debt Service Coverage Ratio (DSCR).

        Intended formula:
        dscr = noi / annual_debt_service
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_grm(purchase_price: Decimal, annual_gross_rent: Decimal) -> Decimal:
        """
        Calculate Gross Rent Multiplier (GRM).

        Intended formula:
        grm = purchase_price / annual_gross_rent
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_monthly_cash_flow(
        effective_gross_income_monthly: Decimal,
        operating_expenses_monthly: Decimal,
        monthly_mortgage: Decimal,
    ) -> Decimal:
        """
        Calculate monthly cash flow after operating costs and debt service.

        Intended formula:
        monthly_cash_flow =
            effective_gross_income_monthly
            - operating_expenses_monthly
            - monthly_mortgage
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_total_cash_invested(
        purchase_price: Decimal,
        down_payment_amount: Decimal,
        closing_costs: Decimal,
        rehab_costs: Decimal,
    ) -> Decimal:
        """
        Calculate total cash invested at acquisition.

        Intended formula from domain docs:
        total_cash_invested = down_payment_amount + closing_costs + rehab_costs

        purchase_price is included in the signature for convenience/validation
        context used by higher-level orchestration.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_equity_buildup(
        loan_amount: Decimal,
        annual_rate: Decimal,
        term_years: int,
        years: int,
    ) -> Decimal:
        """
        Calculate equity created from principal paydown over a hold period.

        Intended approach:
        - Build/derive amortization through `years * 12` payments.
        - Compute remaining loan balance at that point.
        - Equity buildup from paydown = original loan_amount - remaining balance.
        """
        raise NotImplementedError("Developer will implement")

    @staticmethod
    def calculate_irr_projection(deal_inputs: dict, hold_years: int) -> Decimal:
        """
        Calculate projected IRR for a hold period (e.g., 5 or 10 years).

        Intended cash-flow composition per domain docs:
        - Initial investment (negative cash flow)
        - Annual operating cash flows during hold period
        - Exit proceeds at sale:
          projected sale value - selling costs - remaining loan balance
        """
        raise NotImplementedError("Developer will implement")
