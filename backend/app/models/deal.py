from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from app.database import Base
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.property import Property
    from app.models.user import User


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    deal_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    # Purchase details
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    closing_costs: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    rehab_costs: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    after_repair_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Financing
    down_payment_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    loan_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    interest_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 3), nullable=True
    )
    loan_term_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    monthly_mortgage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Income (monthly)
    gross_monthly_rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    other_monthly_income: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Expenses (monthly)
    property_tax_monthly: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    insurance_monthly: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    vacancy_rate_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    maintenance_rate_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    management_fee_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    hoa_monthly: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    utilities_monthly: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Calculated metrics (None until calculator runs)
    noi: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    cap_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    cash_on_cash: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 3), nullable=True
    )
    monthly_cash_flow: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    annual_cash_flow: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    total_cash_invested: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    dscr: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    grm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    irr_5yr: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    irr_10yr: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    equity_buildup_5yr: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    equity_buildup_10yr: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Risk scoring
    risk_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    risk_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    property: Mapped["Property"] = relationship("Property", back_populates="deals")
    user: Mapped["User"] = relationship("User", back_populates="deals")
