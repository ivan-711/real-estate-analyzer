"""Create market_snapshots table.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_snapshots",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("zip_code", sa.String(length=10), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("median_home_value", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("median_rent", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("avg_price_per_sqft", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("avg_days_on_market", sa.Integer(), nullable=True),
        sa.Column("inventory_count", sa.Integer(), nullable=True),
        sa.Column("avg_cap_rate", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("avg_vacancy_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("rent_to_price_ratio", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("yoy_appreciation_pct", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("population_growth_pct", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("data_source", sa.String(length=50), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("zip_code", "snapshot_date", "data_source", name="uq_market_snapshot"),
    )


def downgrade() -> None:
    op.drop_table("market_snapshots")
