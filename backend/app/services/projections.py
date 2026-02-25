"""
Year-by-year financial projections for a saved deal.

All functions are pure (no DB access, no async). Imports amortization and IRR
logic from app.utils.financial; does not duplicate any logic that already exists
there or in deal_calculator.py.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from app.utils.financial import calculate_amortization_schedule, calculate_irr

QUANTIZE_MONEY = Decimal("0.01")
QUANTIZE_RATE = Decimal("0.0001")


def _d(val: Decimal | float | int | None) -> Decimal:
    """Coerce to Decimal; None / falsy becomes 0."""
    if val is None:
        return Decimal("0")
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def _aggregate_amortization_annual(
    loan_amount: Decimal,
    annual_rate: Decimal,
    term_years: int,
    projection_years: int,
) -> list[dict]:
    """Aggregate a monthly amortization schedule into annual buckets.

    Returns a list of length `projection_years`, each dict containing:
        year, principal_paid, interest_paid, ending_balance

    Years beyond the loan payoff date have all-zero values.
    For all-cash purchases (loan_amount <= 0), returns all zeros immediately.
    """
    zero = Decimal("0.00")

    if loan_amount <= 0:
        return [
            {
                "year": y,
                "principal_paid": zero,
                "interest_paid": zero,
                "ending_balance": zero,
            }
            for y in range(1, projection_years + 1)
        ]

    schedule = calculate_amortization_schedule(loan_amount, annual_rate, term_years)

    annual: list[dict] = []
    for year in range(1, projection_years + 1):
        start = (year - 1) * 12
        end = year * 12
        months = schedule[start:end]

        if not months:
            # Loan fully paid off before this year
            annual.append(
                {
                    "year": year,
                    "principal_paid": zero,
                    "interest_paid": zero,
                    "ending_balance": zero,
                }
            )
        else:
            principal_paid = sum(
                (m["principal"] for m in months), zero
            ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
            interest_paid = sum(
                (m["interest"] for m in months), zero
            ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
            ending_balance = months[-1]["remaining_balance"]
            annual.append(
                {
                    "year": year,
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "ending_balance": ending_balance,
                }
            )

    return annual


def _compute_irr(
    total_cash_invested: Decimal,
    yearly_net_cashflows: list[Decimal],
    yearly_balances: list[Decimal],
    yearly_values: list[Decimal],
    hold_years: int,
    selling_cost_pct: Decimal,
) -> Optional[Decimal]:
    """Compute IRR for a given holding period using actual year-by-year cash flows.

    Cash flows passed to calculate_irr:
        [ -total_cash_invested,
          cf_y1, cf_y2, ..., cf_y(N-1),
          cf_yN + exit_proceeds ]

    exit_proceeds = property_value_yN × (1 - selling_cost_pct/100) - loan_balance_yN

    Returns None if hold_years exceeds available data, invested amount is non-positive,
    or IRR fails to converge.
    """
    if hold_years > len(yearly_net_cashflows):
        return None
    if total_cash_invested <= 0:
        return None

    exit_value = yearly_values[hold_years - 1]
    exit_balance = yearly_balances[hold_years - 1]
    selling_cost_rate = selling_cost_pct / 100
    exit_proceeds = (
        exit_value * (1 - selling_cost_rate) - exit_balance
    ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

    cash_flows: list[Decimal] = [-total_cash_invested]
    for i in range(hold_years - 1):
        cash_flows.append(yearly_net_cashflows[i])
    # Final year combines operating cash flow with net sale proceeds.
    cash_flows.append(yearly_net_cashflows[hold_years - 1] + exit_proceeds)

    try:
        return calculate_irr(cash_flows)
    except (ValueError, ZeroDivisionError):
        return None


def compute_yearly_projections(
    purchase_price: Decimal,
    loan_amount: Decimal,
    annual_interest_rate: Decimal,
    loan_term_years: int,
    monthly_mortgage: Decimal,
    gross_monthly_rent: Decimal,
    base_monthly_expenses: Decimal,
    total_cash_invested: Decimal,
    projection_years: int,
    annual_appreciation_pct: Decimal,
    annual_rent_growth_pct: Decimal,
    annual_expense_growth_pct: Decimal,
    selling_cost_pct: Decimal,
) -> dict:
    """Compute year-by-year financial projections for a deal.

    Projection model:
    - Property value: purchase_price × (1 + appreciation_rate)^year
    - Loan balance: from amortization schedule (0 for all-cash)
    - Equity: property_value - loan_balance
    - Gross rent: grows by rent_growth_rate each year (year 1 = base)
    - Expenses: grow by expense_growth_rate each year (year 1 = base)
    - Mortgage: fixed throughout (principal + interest payment never changes)
    - Net cash flow: annual_gross_rent - annual_expenses - annual_mortgage_payment
    - IRR: computed for 5-year and 10-year hold using actual per-year cash flows
      and appreciation-based terminal value. None when projection_years < threshold.

    Returns:
        {
            "yearly": list[dict],      # one dict per year, matching YearlyProjection fields
            "irr_5yr": Decimal | None,
            "irr_10yr": Decimal | None,
        }
    """
    appreciation_rate = _d(annual_appreciation_pct) / 100
    rent_growth_rate = _d(annual_rent_growth_pct) / 100
    expense_growth_rate = _d(annual_expense_growth_pct) / 100

    amort = _aggregate_amortization_annual(
        loan_amount, annual_interest_rate, loan_term_years, projection_years
    )

    yearly: list[dict] = []
    yearly_net_cashflows: list[Decimal] = []
    yearly_balances: list[Decimal] = []
    yearly_values: list[Decimal] = []
    cumulative_cf = Decimal("0.00")

    for year in range(1, projection_years + 1):
        # Compound appreciation
        property_value = (
            _d(purchase_price) * (1 + appreciation_rate) ** year
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

        amort_year = amort[year - 1]
        loan_balance: Decimal = amort_year["ending_balance"]
        principal_paid: Decimal = amort_year["principal_paid"]
        interest_paid: Decimal = amort_year["interest_paid"]

        equity = (property_value - loan_balance).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )

        # Year 1 uses base figures; subsequent years grow from year 1 base.
        rent_factor = (1 + rent_growth_rate) ** (year - 1)
        expense_factor = (1 + expense_growth_rate) ** (year - 1)

        annual_gross_rent = (
            _d(gross_monthly_rent) * 12 * rent_factor
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

        annual_expenses = (
            _d(base_monthly_expenses) * 12 * expense_factor
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

        annual_mortgage_payment = (
            _d(monthly_mortgage) * 12
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

        annual_net_cash_flow = (
            annual_gross_rent - annual_expenses - annual_mortgage_payment
        ).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

        cumulative_cf = (cumulative_cf + annual_net_cash_flow).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )

        yearly_net_cashflows.append(annual_net_cash_flow)
        yearly_balances.append(loan_balance)
        yearly_values.append(property_value)

        yearly.append(
            {
                "year": year,
                "property_value": property_value,
                "loan_balance": loan_balance,
                "equity": equity,
                "principal_paid": principal_paid,
                "interest_paid": interest_paid,
                "annual_gross_rent": annual_gross_rent,
                "annual_expenses": annual_expenses,
                "annual_mortgage_payment": annual_mortgage_payment,
                "annual_net_cash_flow": annual_net_cash_flow,
                "cumulative_cash_flow": cumulative_cf,
            }
        )

    irr_5yr = (
        _compute_irr(
            _d(total_cash_invested),
            yearly_net_cashflows,
            yearly_balances,
            yearly_values,
            5,
            _d(selling_cost_pct),
        )
        if projection_years >= 5
        else None
    )
    irr_10yr = (
        _compute_irr(
            _d(total_cash_invested),
            yearly_net_cashflows,
            yearly_balances,
            yearly_values,
            10,
            _d(selling_cost_pct),
        )
        if projection_years >= 10
        else None
    )

    return {"yearly": yearly, "irr_5yr": irr_5yr, "irr_10yr": irr_10yr}
