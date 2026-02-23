"""
Deal financial metrics calculator.

Uses app.utils.financial for mortgage, amortization, remaining balance, IRR.
All monetary values use Decimal.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.utils.financial import (
    calculate_irr,
    calculate_monthly_mortgage,
    calculate_remaining_balance,
)

QUANTIZE_MONEY = Decimal("0.01")
QUANTIZE_RATE = Decimal("0.0001")


def _d(val: Decimal | float | None) -> Decimal:
    """Coerce to Decimal; None becomes 0."""
    if val is None:
        return Decimal("0")
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


class DealCalculator:
    """Developer-owned financial calculator service for deal metrics."""

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

        Vacancy loss, EGI, operating expenses (excluding debt service), then NOI * 12.
        """
        gross = _d(gross_monthly_rent)
        vacancy_pct = _d(vacancy_rate_pct)
        vacancy_loss = (gross * vacancy_pct / 100).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        egi = (gross + _d(other_monthly_income) - vacancy_loss).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )

        maintenance = (gross * _d(maintenance_rate_pct) / 100).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        management = (gross * _d(management_fee_pct) / 100).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        opex = (
            _d(property_tax_monthly)
            + _d(insurance_monthly)
            + maintenance
            + management
            + _d(hoa_monthly)
            + _d(utilities_monthly)
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

        monthly_noi = (egi - opex).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
        return (monthly_noi * 12).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_cap_rate(noi: Decimal, purchase_price: Decimal) -> Decimal:
        """Cap rate = NOI / purchase_price. Rejects zero or negative price."""
        price = _d(purchase_price)
        if price <= 0:
            raise ValueError("Purchase price must be positive")
        n = _d(noi)
        return (n / price).quantize(QUANTIZE_RATE, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_cash_on_cash(
        annual_cash_flow: Decimal,
        total_cash_invested: Decimal,
    ) -> Decimal:
        """Cash-on-cash = annual_cash_flow / total_cash_invested."""
        tci = _d(total_cash_invested)
        if tci <= 0:
            raise ValueError("Total cash invested must be positive")
        return (_d(annual_cash_flow) / tci).quantize(
            QUANTIZE_RATE, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_dscr(noi: Decimal, annual_debt_service: Decimal) -> Decimal | None:
        """DSCR = NOI / annual_debt_service. Returns None for all-cash (zero debt)."""
        ads = _d(annual_debt_service)
        if ads == 0:
            return None
        return (_d(noi) / ads).quantize(QUANTIZE_RATE, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_grm(purchase_price: Decimal, annual_gross_rent: Decimal) -> Decimal:
        """GRM = purchase_price / annual_gross_rent."""
        rent = _d(annual_gross_rent)
        if rent <= 0:
            raise ValueError("Annual gross rent must be positive")
        return (_d(purchase_price) / rent).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_monthly_cash_flow(
        effective_gross_income_monthly: Decimal,
        operating_expenses_monthly: Decimal,
        monthly_mortgage: Decimal,
    ) -> Decimal:
        """Monthly cash flow = EGI - operating expenses - monthly mortgage."""
        return (
            _d(effective_gross_income_monthly)
            - _d(operating_expenses_monthly)
            - _d(monthly_mortgage)
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_total_cash_invested(
        purchase_price: Decimal,
        down_payment_amount: Decimal,
        closing_costs: Decimal,
        rehab_costs: Decimal,
    ) -> Decimal:
        """Total cash invested = down_payment + closing_costs + rehab_costs."""
        return (_d(down_payment_amount) + _d(closing_costs) + _d(rehab_costs)).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_equity_buildup(
        loan_amount: Decimal,
        annual_rate: Decimal,
        term_years: int,
        years: int,
    ) -> Decimal:
        """Equity from principal paydown over `years` (loan_amount - remaining_balance)."""
        loan = _d(loan_amount)
        if loan <= 0:
            return Decimal("0").quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
        remaining = calculate_remaining_balance(
            loan, _d(annual_rate), term_years, years
        )
        return (loan - remaining).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_irr_projection(deal_inputs: dict, hold_years: int) -> Decimal:
        """
        Projected IRR: initial outflow, annual cash flows, then exit (sale - costs - remaining balance).
        Sale price = after_repair_value or purchase_price; selling costs = 0 if not provided.
        """
        purchase_price = _d(deal_inputs.get("purchase_price"))
        total_cash_invested = _d(deal_inputs.get("total_cash_invested"))
        annual_cash_flow = _d(deal_inputs.get("annual_cash_flow"))
        loan_amount = _d(deal_inputs.get("loan_amount"))
        interest_rate = _d(deal_inputs.get("interest_rate"))
        loan_term_years = deal_inputs.get("loan_term_years") or 30
        if isinstance(loan_term_years, float):
            loan_term_years = int(loan_term_years)

        if total_cash_invested <= 0:
            total_cash_invested = purchase_price  # fallback for missing

        sale_price = _d(
            deal_inputs.get("after_repair_value") or deal_inputs.get("purchase_price")
        )
        selling_costs = _d(deal_inputs.get("selling_costs", 0))
        remaining_balance = Decimal("0")
        if loan_amount > 0 and hold_years < loan_term_years:
            remaining_balance = calculate_remaining_balance(
                loan_amount, interest_rate, loan_term_years, hold_years
            )

        cash_flows: list[Decimal] = [-total_cash_invested]
        for _ in range(hold_years):
            cash_flows.append(annual_cash_flow)
        exit_proceeds = (sale_price - selling_costs - remaining_balance).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        cash_flows.append(exit_proceeds)

        irr_decimal = calculate_irr(cash_flows)
        return irr_decimal

    @staticmethod
    def calculate_all(deal_inputs: dict) -> dict:
        """
        Compute all derived metrics from deal_inputs.
        Resolves loan_amount and monthly_mortgage if missing; returns dict for CALCULATED_METRIC_FIELDS.
        """
        p = deal_inputs
        purchase_price = _d(p.get("purchase_price"))
        if purchase_price <= 0:
            raise ValueError("purchase_price must be positive")

        down_pct = _d(p.get("down_payment_pct") or 20)
        if p.get("loan_amount") is None:
            loan_amount = (purchase_price - purchase_price * down_pct / 100).quantize(
                QUANTIZE_MONEY, rounding=ROUND_HALF_UP
            )
        else:
            loan_amount = _d(p.get("loan_amount"))

        interest_rate = _d(p.get("interest_rate") or 0)
        loan_term_years = p.get("loan_term_years") or 30
        if isinstance(loan_term_years, float):
            loan_term_years = int(loan_term_years)

        monthly_mortgage = _d(p.get("monthly_mortgage"))
        if monthly_mortgage == 0 and loan_amount > 0 and interest_rate >= 0:
            monthly_mortgage = calculate_monthly_mortgage(
                loan_amount, interest_rate, loan_term_years
            )

        gross_monthly_rent = _d(p.get("gross_monthly_rent"))
        vacancy_rate_pct = _d(p.get("vacancy_rate_pct") or 5)
        other_monthly_income = _d(p.get("other_monthly_income"))
        property_tax_monthly = _d(p.get("property_tax_monthly"))
        insurance_monthly = _d(p.get("insurance_monthly"))
        maintenance_rate_pct = _d(p.get("maintenance_rate_pct") or 5)
        management_fee_pct = _d(p.get("management_fee_pct") or 10)
        hoa_monthly = _d(p.get("hoa_monthly"))
        utilities_monthly = _d(p.get("utilities_monthly"))

        noi = DealCalculator.calculate_noi(
            gross_monthly_rent=gross_monthly_rent,
            vacancy_rate_pct=vacancy_rate_pct,
            property_tax_monthly=property_tax_monthly,
            insurance_monthly=insurance_monthly,
            maintenance_rate_pct=maintenance_rate_pct,
            management_fee_pct=management_fee_pct,
            hoa_monthly=hoa_monthly,
            utilities_monthly=utilities_monthly,
            other_monthly_income=other_monthly_income,
        )

        vacancy_loss = (gross_monthly_rent * vacancy_rate_pct / 100).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        egi_monthly = (
            gross_monthly_rent + other_monthly_income - vacancy_loss
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
        maintenance = (gross_monthly_rent * maintenance_rate_pct / 100).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        management = (gross_monthly_rent * management_fee_pct / 100).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        opex_monthly = (
            property_tax_monthly
            + insurance_monthly
            + maintenance
            + management
            + hoa_monthly
            + utilities_monthly
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

        monthly_cash_flow = DealCalculator.calculate_monthly_cash_flow(
            egi_monthly, opex_monthly, monthly_mortgage
        )
        annual_cash_flow = (monthly_cash_flow * 12).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )

        down_payment_amount = (purchase_price * down_pct / 100).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        closing_costs = _d(p.get("closing_costs"))
        rehab_costs = _d(p.get("rehab_costs"))
        total_cash_invested = DealCalculator.calculate_total_cash_invested(
            purchase_price, down_payment_amount, closing_costs, rehab_costs
        )

        cap_rate = DealCalculator.calculate_cap_rate(noi, purchase_price)
        annual_gross_rent = (gross_monthly_rent * 12).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        grm = DealCalculator.calculate_grm(purchase_price, annual_gross_rent)
        annual_debt_service = (monthly_mortgage * 12).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        dscr = DealCalculator.calculate_dscr(noi, annual_debt_service)
        if total_cash_invested > 0:
            cash_on_cash = DealCalculator.calculate_cash_on_cash(
                annual_cash_flow, total_cash_invested
            )
        else:
            cash_on_cash = None

        equity_5 = (
            DealCalculator.calculate_equity_buildup(
                loan_amount, interest_rate, loan_term_years, 5
            )
            if loan_amount > 0
            else Decimal("0")
        )
        equity_10 = (
            DealCalculator.calculate_equity_buildup(
                loan_amount, interest_rate, loan_term_years, 10
            )
            if loan_amount > 0
            else Decimal("0")
        )

        inputs_for_irr = {
            **p,
            "purchase_price": purchase_price,
            "total_cash_invested": total_cash_invested,
            "annual_cash_flow": annual_cash_flow,
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "loan_term_years": loan_term_years,
            "after_repair_value": p.get("after_repair_value") or purchase_price,
        }
        irr_5yr = None
        irr_10yr = None
        try:
            irr_5yr = DealCalculator.calculate_irr_projection(inputs_for_irr, 5)
        except (ValueError, ZeroDivisionError):
            pass
        try:
            irr_10yr = DealCalculator.calculate_irr_projection(inputs_for_irr, 10)
        except (ValueError, ZeroDivisionError):
            pass

        return {
            "noi": noi,
            "cap_rate": cap_rate,
            "cash_on_cash": cash_on_cash,
            "monthly_cash_flow": monthly_cash_flow,
            "annual_cash_flow": annual_cash_flow,
            "total_cash_invested": total_cash_invested,
            "dscr": dscr,
            "grm": grm,
            "irr_5yr": irr_5yr,
            "irr_10yr": irr_10yr,
            "equity_buildup_5yr": equity_5,
            "equity_buildup_10yr": equity_10,
        }
