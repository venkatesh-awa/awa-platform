"""initial schema - auctions and bids

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-03

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auctions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="scheduled"),
        sa.Column("starting_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("reserve_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("starting_price >= 0", name="ck_auction_starting_price_nonneg"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_auction_ends_after_starts"),
    )
    op.create_index("ix_auctions_vehicle_id", "auctions", ["vehicle_id"])
    op.create_index("ix_auctions_status_ends_at", "auctions", ["status", "ends_at"])

    op.create_table(
        "bids",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "auction_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("auctions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bidder_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("kafka_partition", sa.Integer(), nullable=True),
        sa.Column("kafka_offset", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_bid_amount_positive"),
        sa.CheckConstraint("status in ('pending','accepted','rejected')", name="ck_bid_status_valid"),
    )
    op.create_index("ix_bids_bidder_id", "bids", ["bidder_id"])
    op.create_index("ix_bids_auction_amount", "bids", ["auction_id", "amount"])
    op.create_index(
        "uq_bids_kafka_position",
        "bids",
        ["kafka_partition", "kafka_offset"],
        unique=True,
        mssql_where=sa.text("kafka_offset IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_table("bids")
    op.drop_table("auctions")
