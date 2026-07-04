"""remove card fields from featured auction placements

Revision ID: 0007_featured_cards_split
Revises: 0006_vehicle_listings
Create Date: 2026-07-04

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_featured_cards_split"
down_revision: str | None = "0006_vehicle_listings"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


CARD_COLUMNS = (
    "countdown_label",
    "bid_amount",
    "location_ar",
    "location_en",
    "mileage",
    "lot_number",
    "detail_url",
    "image_url",
    "title_ar",
    "title_en",
)


def upgrade() -> None:
    for column_name in CARD_COLUMNS:
        op.drop_column("featured_auctions", column_name)


def downgrade() -> None:
    op.add_column("featured_auctions", sa.Column("title_en", sa.Unicode(length=200), nullable=True))
    op.add_column("featured_auctions", sa.Column("title_ar", sa.Unicode(length=200), nullable=True))
    op.add_column("featured_auctions", sa.Column("image_url", sa.String(length=500), nullable=True))
    op.add_column("featured_auctions", sa.Column("detail_url", sa.String(length=500), nullable=True))
    op.add_column("featured_auctions", sa.Column("lot_number", sa.String(length=50), nullable=True))
    op.add_column("featured_auctions", sa.Column("mileage", sa.String(length=50), nullable=True))
    op.add_column("featured_auctions", sa.Column("location_en", sa.Unicode(length=100), nullable=True))
    op.add_column("featured_auctions", sa.Column("location_ar", sa.Unicode(length=100), nullable=True))
    op.add_column("featured_auctions", sa.Column("bid_amount", sa.String(length=50), nullable=True))
    op.add_column("featured_auctions", sa.Column("countdown_label", sa.String(length=50), nullable=True))
