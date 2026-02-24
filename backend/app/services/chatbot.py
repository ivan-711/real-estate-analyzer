"""Chatbot service: LLM prompt engineering and context injection.

This module is DEVELOPER-OWNED. The scaffolding (DB query, serialization
structure, streaming call) was generated; the developer will refine the
system prompt wording, deal summary format, and model choice.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import anthropic
from app.config import settings
from app.models.deal import Deal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

# --- Configuration constants ------------------------------------------------

MAX_DEALS = 10
MAX_HISTORY = 10
MAX_TOKENS = 1024
# claude-haiku-4-5: fast and affordable for deal Q&A; change as needed
MODEL = "claude-haiku-4-5"


# --- Formatting helpers ------------------------------------------------------


def _fmt_money(val: Decimal | None) -> str:
    """Format a Decimal as $X,XXX or 'N/A'."""
    if val is None:
        return "N/A"
    return f"${val:,.0f}" if val == int(val) else f"${val:,.2f}"


def _fmt_pct(val: Decimal | None) -> str:
    """Format a Decimal as X.XX% or 'N/A'."""
    if val is None:
        return "N/A"
    return f"{val:.2f}%"


def _fmt_ratio(val: Decimal | None) -> str:
    """Format a Decimal as X.XXX or 'N/A'."""
    if val is None:
        return "N/A"
    return f"{val:.3f}"


def _fmt_grm(val: Decimal | None) -> str:
    """Format GRM as X.XX or 'N/A'."""
    if val is None:
        return "N/A"
    return f"{val:.2f}"


def _risk_label(score: Decimal | None) -> str:
    if score is None:
        return "N/A"
    s = float(score)
    if s <= 33:
        return "Low Risk"
    if s <= 66:
        return "Moderate Risk"
    return "High Risk"


# --- Deal serialization (ARCHITECTURE.md format) -----------------------------


def _serialize_deal(deal: Deal) -> str:
    """Serialize a single deal into the compact text block from ARCHITECTURE."""
    prop = deal.property

    address_line = f"{prop.address}, {prop.city} {prop.state} {prop.zip_code}"

    type_parts: list[str] = [prop.property_type.replace("_", " ").title()]
    if prop.bedrooms is not None:
        bath = f"{prop.bathrooms:g}" if prop.bathrooms is not None else "?"
        type_parts.append(f"{prop.bedrooms} bed / {bath} bath")
    if prop.square_footage is not None:
        type_parts.append(f"{prop.square_footage:,} sqft")
    if prop.year_built is not None:
        type_parts.append(f"Built {prop.year_built}")
    type_line = " | ".join(type_parts)

    down_dollars = "N/A"
    if deal.purchase_price and deal.down_payment_pct is not None:
        down_dollars = _fmt_money(
            deal.purchase_price * deal.down_payment_pct / Decimal("100")
        )

    purchase_line = (
        f"Purchase: {_fmt_money(deal.purchase_price)} | "
        f"Down: {_fmt_pct(deal.down_payment_pct)} ({down_dollars}) | "
        f"Loan: {_fmt_money(deal.loan_amount)} @ {_fmt_pct(deal.interest_rate)}"
    )

    income_line = (
        f"Income: {_fmt_money(deal.gross_monthly_rent)}/mo rent | "
        f"Vacancy: {_fmt_pct(deal.vacancy_rate_pct)}"
    )

    cash_flow_line = (
        f"Cash Flow: {_fmt_money(deal.monthly_cash_flow)}/mo | "
        f"{_fmt_money(deal.annual_cash_flow)}/yr"
    )

    metrics_line = (
        f"Metrics: NOI {_fmt_money(deal.noi)} | "
        f"Cap Rate {_fmt_pct(deal.cap_rate)} | "
        f"CoC {_fmt_pct(deal.cash_on_cash)} | "
        f"DSCR {_fmt_ratio(deal.dscr)} | "
        f"GRM {_fmt_grm(deal.grm)}"
    )

    risk_line = (
        f"Risk: {_fmt_ratio(deal.risk_score).rstrip('0').rstrip('.')}/100 "
        f"({_risk_label(deal.risk_score)})"
    )

    irr_line = (
        f"IRR: {_fmt_pct(deal.irr_5yr)} (5yr) | " f"{_fmt_pct(deal.irr_10yr)} (10yr)"
    )

    return (
        f'DEAL: "{address_line}"\n'
        f"Type: {type_line}\n"
        f"{purchase_line}\n"
        f"{income_line}\n"
        f"{cash_flow_line}\n"
        f"{metrics_line}\n"
        f"{risk_line}\n"
        f"{irr_line}"
    )


def _build_portfolio_summary(deals: list[Deal]) -> str:
    """Build a short portfolio summary header from the deals list."""
    count = len(deals)
    cash_flows = [d.monthly_cash_flow for d in deals if d.monthly_cash_flow is not None]
    cap_rates = [d.cap_rate for d in deals if d.cap_rate is not None]
    risk_scores = [d.risk_score for d in deals if d.risk_score is not None]

    total_cf = _fmt_money(sum(cash_flows)) if cash_flows else "N/A"
    avg_cap = _fmt_pct(sum(cap_rates) / len(cap_rates)) if cap_rates else "N/A"
    avg_risk = (
        f"{sum(risk_scores) / len(risk_scores):.0f}/100" if risk_scores else "N/A"
    )

    return (
        f"PORTFOLIO SUMMARY:\n"
        f"Total Properties: {count}\n"
        f"Total Monthly Cash Flow: {total_cf}\n"
        f"Average Cap Rate: {avg_cap}\n"
        f"Average Risk Score: {avg_risk}"
    )


# --- System prompt -----------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """\
You are a real estate investment analyst assistant for the MidwestDealAnalyzer \
platform. You have access to the user's complete property portfolio and deal \
analyses below. Answer questions using the provided deal data. If asked to \
run scenarios (e.g., "what if vacancy goes to 10%?"), recalculate the relevant \
metrics using the formulas you know. Always cite specific numbers from the \
user's actual deals. If you don't have enough data to answer, say so.

{context}"""

NO_DEALS_CONTEXT = """\
The user has no saved deals yet. Help them understand what the platform does \
and encourage them to analyze their first property."""


def _build_system_prompt(deals: list[Deal]) -> str:
    """Assemble the full system prompt with portfolio data."""
    if not deals:
        return SYSTEM_PROMPT_TEMPLATE.format(context=NO_DEALS_CONTEXT)

    summary = _build_portfolio_summary(deals)
    serialized = "\n\n".join(_serialize_deal(d) for d in deals)
    context = f"{summary}\n\nUSER'S DEALS:\n{serialized}"
    return SYSTEM_PROMPT_TEMPLATE.format(context=context)


# --- Main entry point --------------------------------------------------------


async def stream_chat_response(
    user_id: uuid.UUID,
    message: str,
    history: list[dict[str, Any]],
    db: AsyncSession,
) -> AsyncIterator[str]:
    """Stream assistant response chunks for the given user message.

    Loads the user's deals from the DB, serializes them into context,
    builds a system prompt, and streams from the Anthropic Claude API.

    Yields:
        Text chunks (strings) for the router to emit as SSE events.
    """
    # Guard: missing API key
    if not settings.anthropic_api_key:
        yield "Chat is not configured. Please set ANTHROPIC_API_KEY."
        return

    # Load user deals with their properties
    try:
        result = await db.execute(
            select(Deal)
            .where(Deal.user_id == user_id)
            .options(selectinload(Deal.property))
            .order_by(Deal.updated_at.desc())
            .limit(MAX_DEALS)
        )
        deals = list(result.scalars().all())
    except Exception:
        logger.exception("Failed to load deals for user %s", user_id)
        yield "Unable to load your deal data right now. Please try again."
        return

    # Build system prompt with portfolio context
    system_prompt = _build_system_prompt(deals)

    # Build messages: capped history + current user message
    capped_history = history[-MAX_HISTORY:]
    messages: list[dict[str, str]] = [
        {"role": h["role"], "content": h["content"]} for h in capped_history
    ]
    messages.append({"role": "user", "content": message})

    # Stream from Claude
    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        async with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except anthropic.APIError as exc:
        logger.exception("Anthropic API error: %s", exc)
        yield "The AI assistant is temporarily unavailable. Please try again."
    except Exception:
        logger.exception("Unexpected error streaming chat response")
        yield "The AI assistant encountered an error. Please try again."
