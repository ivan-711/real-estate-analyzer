"""Create properties and deals tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-19

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "properties",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("zip_code", sa.String(length=10), nullable=False),
        sa.Column("county", sa.String(length=100), nullable=True),
        sa.Column("property_type", sa.String(length=50), nullable=False),
        sa.Column("num_units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bedrooms", sa.Integer(), nullable=True),
        sa.Column("bathrooms", sa.Numeric(3, 1), nullable=True),
        sa.Column("square_footage", sa.Integer(), nullable=True),
        sa.Column("lot_size", sa.Integer(), nullable=True),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("rentcast_id", sa.String(length=100), nullable=True),
        sa.Column("mashvisor_id", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "deals",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("deal_name", sa.String(length=100), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="draft"
        ),
        sa.Column("purchase_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("closing_costs", sa.Numeric(12, 2), nullable=True),
        sa.Column("rehab_costs", sa.Numeric(12, 2), nullable=True),
        sa.Column("after_repair_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("down_payment_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("loan_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("interest_rate", sa.Numeric(5, 3), nullable=True),
        sa.Column("loan_term_years", sa.Integer(), nullable=True),
        sa.Column("monthly_mortgage", sa.Numeric(12, 2), nullable=True),
        sa.Column("gross_monthly_rent", sa.Numeric(12, 2), nullable=False),
        sa.Column("other_monthly_income", sa.Numeric(12, 2), nullable=True),
        sa.Column("property_tax_monthly", sa.Numeric(12, 2), nullable=True),
        sa.Column("insurance_monthly", sa.Numeric(12, 2), nullable=True),
        sa.Column("vacancy_rate_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("maintenance_rate_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("management_fee_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("hoa_monthly", sa.Numeric(12, 2), nullable=True),
        sa.Column("utilities_monthly", sa.Numeric(12, 2), nullable=True),
        sa.Column("noi", sa.Numeric(12, 2), nullable=True),
        sa.Column("cap_rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("cash_on_cash", sa.Numeric(6, 3), nullable=True),
        sa.Column("monthly_cash_flow", sa.Numeric(12, 2), nullable=True),
        sa.Column("annual_cash_flow", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_cash_invested", sa.Numeric(12, 2), nullable=True),
        sa.Column("dscr", sa.Numeric(6, 3), nullable=True),
        sa.Column("grm", sa.Numeric(6, 2), nullable=True),
        sa.Column("irr_5yr", sa.Numeric(6, 3), nullable=True),
        sa.Column("irr_10yr", sa.Numeric(6, 3), nullable=True),
        sa.Column("equity_buildup_5yr", sa.Numeric(12, 2), nullable=True),
        sa.Column("equity_buildup_10yr", sa.Numeric(12, 2), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("risk_factors", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("deals")
    op.drop_table("properties")
