"""
Financial math utilities: mortgage payment, amortization, IRR, remaining balance.

All functions use Decimal for precision. Used by deal_calculator and risk_engine.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

QUANTIZE_MONEY = Decimal("0.01")
QUANTIZE_RATE = Decimal("0.0001")


def calculate_monthly_mortgage(
    loan_amount: Decimal,
    annual_rate: Decimal,
    term_years: int,
) -> Decimal:
    """
    Calculate fixed-rate monthly mortgage payment (principal + interest).

    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where P is loan amount, r is monthly rate (annual_rate / 12), and
    n is total payments (term_years * 12).

    Edge cases: zero rate returns loan/n; zero loan returns 0.
    """
    if loan_amount < 0:
        raise ValueError("loan_amount must be non-negative")
    if term_years < 1:
        raise ValueError("term_years must be at least 1")
    if annual_rate < 0:
        raise ValueError("annual_rate must be non-negative")

    n = term_years * 12
    if loan_amount == 0:
        return Decimal("0").quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

    r = (annual_rate / 100) / 12 if annual_rate != 0 else Decimal("0")
    if r == 0:
        return (loan_amount / n).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

    one_plus_r = Decimal("1") + r
    one_plus_r_n = one_plus_r**n
    payment = loan_amount * (r * one_plus_r_n) / (one_plus_r_n - 1)
    return payment.quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)


def calculate_amortization_schedule(
    loan_amount: Decimal,
    annual_rate: Decimal,
    term_years: int,
) -> list[dict]:
    """
    Build payment-by-payment amortization schedule for a fixed-rate loan.

    Each row: payment_number, payment, principal, interest, remaining_balance.
    """
    if loan_amount < 0 or term_years < 1:
        raise ValueError("loan_amount and term_years must be positive")
    if annual_rate < 0:
        raise ValueError("annual_rate must be non-negative")

    n = term_years * 12
    payment = calculate_monthly_mortgage(loan_amount, annual_rate, term_years)
    r = (annual_rate / 100) / 12 if annual_rate != 0 else Decimal("0")

    schedule: list[dict] = []
    remaining = loan_amount

    if loan_amount == 0:
        return schedule

    if r == 0:
        principal_per_period = (loan_amount / n).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        for i in range(1, n + 1):
            principal = principal_per_period if i < n else remaining
            interest = Decimal("0")
            remaining = remaining - principal
            if remaining < 0:
                remaining = Decimal("0")
            schedule.append(
                {
                    "payment_number": i,
                    "payment": payment,
                    "principal": principal,
                    "interest": interest,
                    "remaining_balance": remaining.quantize(
                        QUANTIZE_MONEY, rounding=ROUND_HALF_UP
                    ),
                }
            )
        return schedule

    for i in range(1, n + 1):
        interest = (remaining * r).quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
        principal = (payment - interest).quantize(
            QUANTIZE_MONEY, rounding=ROUND_HALF_UP
        )
        remaining = remaining - principal
        if remaining < 0:
            remaining = Decimal("0")
        schedule.append(
            {
                "payment_number": i,
                "payment": payment,
                "principal": principal,
                "interest": interest,
                "remaining_balance": remaining.quantize(
                    QUANTIZE_MONEY, rounding=ROUND_HALF_UP
                ),
            }
        )
    return schedule


def calculate_irr(cash_flows: list[Decimal]) -> Decimal:
    """
    Calculate Internal Rate of Return (IRR) for a sequence of cash flows.

    Cash flows: CF[0] initial (negative), then period flows.
    Returns the discount rate (as decimal, e.g. 0.10 = 10%) where NPV = 0.
    """
    if not cash_flows or len(cash_flows) < 2:
        raise ValueError("cash_flows must have at least 2 elements")

    try:
        import numpy_financial as npf
    except ImportError:
        pass
    else:
        cf_float = [float(c) for c in cash_flows]
        irr_float = npf.irr(cf_float)
        if irr_float is None:
            raise ValueError("IRR did not converge")
        return Decimal(str(irr_float)).quantize(QUANTIZE_RATE, rounding=ROUND_HALF_UP)

    # Newton's method: find r such that NPV(r) = 0
    def npv(r: Decimal) -> Decimal:
        total = Decimal("0")
        for t, cf in enumerate(cash_flows):
            if r == Decimal("-1"):
                return Decimal("0")  # avoid division by zero in derivative
            total += cf / ((1 + r) ** t)
        return total

    def npv_prime(r: Decimal) -> Decimal:
        total = Decimal("0")
        for t, cf in enumerate(cash_flows):
            if t == 0:
                continue
            total -= t * cf / ((1 + r) ** (t + 1))
        return total

    r = Decimal("0.1")  # initial guess 10%
    for _ in range(100):
        val = npv(r)
        if abs(val) < Decimal("0.0001"):
            return r.quantize(QUANTIZE_RATE, rounding=ROUND_HALF_UP)
        der = npv_prime(r)
        if der == 0:
            break
        r = r - val / der
        if r < Decimal("-0.99"):
            r = Decimal("-0.99")
    raise ValueError("IRR did not converge")


def calculate_remaining_balance(
    loan_amount: Decimal,
    annual_rate: Decimal,
    term_years: int,
    years_elapsed: int,
) -> Decimal:
    """
    Calculate loan principal remaining after a given number of years.

    Uses amortization: balance after years_elapsed * 12 payments.
    """
    if loan_amount <= 0 or term_years < 1:
        raise ValueError("loan_amount and term_years must be positive")
    if annual_rate < 0:
        raise ValueError("annual_rate must be non-negative")
    if years_elapsed <= 0:
        return loan_amount.quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
    if years_elapsed >= term_years:
        return Decimal("0").quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)

    schedule = calculate_amortization_schedule(loan_amount, annual_rate, term_years)
    months = years_elapsed * 12
    if months >= len(schedule):
        return Decimal("0").quantize(QUANTIZE_MONEY, rounding=ROUND_HALF_UP)
    row = schedule[months - 1]
    return row["remaining_balance"]
