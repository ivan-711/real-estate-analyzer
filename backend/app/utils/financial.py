from __future__ import annotations

from decimal import Decimal


def calculate_monthly_mortgage(
    loan_amount: Decimal,
    annual_rate: Decimal,
    term_years: int,
) -> Decimal:
    """
    Calculate fixed-rate monthly mortgage payment (principal + interest).

    Intended formula from domain docs:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where P is loan amount, r is monthly rate (annual_rate / 12), and
    n is total payments (term_years * 12).
    """
    raise NotImplementedError("Developer will implement")


def calculate_amortization_schedule(
    loan_amount: Decimal,
    annual_rate: Decimal,
    term_years: int,
) -> list[dict]:
    """
    Build payment-by-payment amortization schedule for a fixed-rate loan.

    Intended behavior: split each monthly payment into interest and principal,
    reduce the remaining balance over time, and return structured rows for
    downstream metrics (e.g., equity buildup and remaining balance by year).
    """
    raise NotImplementedError("Developer will implement")


def calculate_irr(cash_flows: list[Decimal]) -> Decimal:
    """
    Calculate Internal Rate of Return (IRR) for a sequence of cash flows.

    Intended behavior: return the discount rate where net present value equals
    zero, using a stable numerical method suitable for real-estate cash-flow
    projections.
    """
    raise NotImplementedError("Developer will implement")


def calculate_remaining_balance(
    loan_amount: Decimal,
    annual_rate: Decimal,
    term_years: int,
    years_elapsed: int,
) -> Decimal:
    """
    Calculate loan principal remaining after a given number of years.

    Intended behavior: use amortization math to compute balance after
    years_elapsed * 12 payments for a fixed-rate mortgage.
    """
    raise NotImplementedError("Developer will implement")
