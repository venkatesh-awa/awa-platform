"""link vehicle_listings to sellers and bids to bidders

Revision ID: 0009_vehicle_seller_bid_fk
Revises: 0008_auction_vehicle_fk
Create Date: 2026-07-04

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_vehicle_seller_bid_fk"
down_revision: str | None = "0008_auction_vehicle_fk"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # vehicle_listings.seller_id: nullable, since admin-curated/existing
    # listings (see 0006's backfill) have no seller of record.
    op.add_column(
        "vehicle_listings",
        sa.Column("seller_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_vehicle_listings_seller_id", "vehicle_listings", ["seller_id"])
    op.create_foreign_key(
        "fk_vehicle_listings_seller_id",
        "vehicle_listings",
        "users",
        ["seller_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # bids.bidder_id already exists (0001_initial) as a bare UUID; tie it to
    # the local users table now that Bid.bidder_id is always populated from
    # the locally-authenticated user (see services/bid_service.submit_bid).
    op.create_foreign_key(
        "fk_bids_bidder_id",
        "bids",
        "users",
        ["bidder_id"],
        ["id"],
        ondelete="NO ACTION",
    )


def downgrade() -> None:
    op.drop_constraint("fk_bids_bidder_id", "bids", type_="foreignkey")
    op.drop_constraint("fk_vehicle_listings_seller_id", "vehicle_listings", type_="foreignkey")
    op.drop_index("ix_vehicle_listings_seller_id", table_name="vehicle_listings")
    op.drop_column("vehicle_listings", "seller_id")
