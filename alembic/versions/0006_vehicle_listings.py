"""vehicle listings backing featured auction cards

Revision ID: 0006_vehicle_listings
Revises: 0005_featured_auction_tabs
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_vehicle_listings"
down_revision: str | None = "0005_featured_auction_tabs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vehicle_listings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("title_en", sa.Unicode(length=200), nullable=False),
        sa.Column("title_ar", sa.Unicode(length=200), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("detail_url", sa.String(length=500), nullable=False),
        sa.Column("lot_number", sa.String(length=50), nullable=True),
        sa.Column("mileage", sa.String(length=50), nullable=True),
        sa.Column("location_en", sa.Unicode(length=100), nullable=True),
        sa.Column("location_ar", sa.Unicode(length=100), nullable=True),
        sa.Column("bid_amount", sa.String(length=50), nullable=True),
        sa.Column("countdown_label", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column(
        "featured_auctions",
        sa.Column("vehicle_listing_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_featured_auctions_vehicle_listing_id",
        "featured_auctions",
        ["vehicle_listing_id"],
    )
    op.create_foreign_key(
        "fk_featured_auctions_vehicle_listing_id",
        "featured_auctions",
        "vehicle_listings",
        ["vehicle_listing_id"],
        ["id"],
        ondelete="SET NULL",
    )
    _backfill_vehicle_listings()


def _backfill_vehicle_listings() -> None:
    connection = op.get_bind()
    featured_rows = connection.execute(
        sa.text(
            """
            SELECT id,
                   title_en,
                   title_ar,
                   image_url,
                   detail_url,
                   lot_number,
                   mileage,
                   location_en,
                   location_ar,
                   bid_amount,
                   countdown_label
            FROM featured_auctions
            WHERE vehicle_listing_id IS NULL
            """
        )
    ).mappings()

    for row in featured_rows:
        listing_id = str(uuid.uuid4())
        connection.execute(
            sa.text(
                """
                INSERT INTO vehicle_listings (
                    id,
                    title_en,
                    title_ar,
                    image_url,
                    detail_url,
                    lot_number,
                    mileage,
                    location_en,
                    location_ar,
                    bid_amount,
                    countdown_label,
                    is_active
                )
                VALUES (
                    :id,
                    :title_en,
                    :title_ar,
                    :image_url,
                    :detail_url,
                    :lot_number,
                    :mileage,
                    :location_en,
                    :location_ar,
                    :bid_amount,
                    :countdown_label,
                    1
                )
                """
            ),
            {
                "id": listing_id,
                "title_en": row["title_en"],
                "title_ar": row["title_ar"],
                "image_url": row["image_url"],
                "detail_url": row["detail_url"] or "#",
                "lot_number": row["lot_number"],
                "mileage": row["mileage"],
                "location_en": row["location_en"],
                "location_ar": row["location_ar"],
                "bid_amount": row["bid_amount"],
                "countdown_label": row["countdown_label"],
            },
        )
        connection.execute(
            sa.text(
                """
                UPDATE featured_auctions
                SET vehicle_listing_id = :vehicle_listing_id
                WHERE id = :featured_auction_id
                """
            ),
            {
                "vehicle_listing_id": listing_id,
                "featured_auction_id": row["id"],
            },
        )


def downgrade() -> None:
    op.drop_constraint(
        "fk_featured_auctions_vehicle_listing_id",
        "featured_auctions",
        type_="foreignkey",
    )
    op.drop_index("ix_featured_auctions_vehicle_listing_id", table_name="featured_auctions")
    op.drop_column("featured_auctions", "vehicle_listing_id")
    op.drop_table("vehicle_listings")
