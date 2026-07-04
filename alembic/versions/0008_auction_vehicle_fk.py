"""link auctions to vehicle_listings

Revision ID: 0008_auction_vehicle_fk
Revises: 0007_featured_cards_split
Create Date: 2026-07-04

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008_auction_vehicle_fk"
down_revision: str | None = "0007_featured_cards_split"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # auctions.vehicle_id has existed since 0001_initial as a bare UUID column
    # (vehicle_listings didn't exist yet). Now that it does, tie the two
    # tables together so the relationship is enforced at the DB level instead
    # of relying on application code to keep them in sync.
    op.create_foreign_key(
        "fk_auctions_vehicle_id",
        "auctions",
        "vehicle_listings",
        ["vehicle_id"],
        ["id"],
        ondelete="NO ACTION",
    )


def downgrade() -> None:
    op.drop_constraint("fk_auctions_vehicle_id", "auctions", type_="foreignkey")
