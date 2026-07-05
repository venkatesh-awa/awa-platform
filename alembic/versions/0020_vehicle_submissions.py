"""extend vehicle_listings with the seller "Add a New Car" intake fields,
instead of a separate table - a submission is a vehicle listing (unpublished
until reviewed), not a distinct entity.

Pre-existing rows are backfilled to status="published" since they predate
this intake flow and are, by definition, already live/curated listings.

Revision ID: 0020_vehicle_submissions
Revises: 0019_vehicle_lookup_tables
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020_vehicle_submissions"
down_revision: str | None = "0019_vehicle_lookup_tables"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vehicle_listings", sa.Column("chassis_number", sa.String(length=100), nullable=True))
    # Filtered index, not a plain unique index: every pre-existing row will
    # have chassis_number NULL after this ADD COLUMN, and SQL Server's plain
    # unique index only tolerates a single NULL (unlike Postgres).
    op.execute(
        "CREATE UNIQUE INDEX ix_vehicle_listings_chassis_number ON vehicle_listings (chassis_number) "
        "WHERE chassis_number IS NOT NULL"
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "make_id", sa.Uuid(as_uuid=True), sa.ForeignKey("vehicle_makes.id", ondelete="NO ACTION"), nullable=True
        ),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "model_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("vehicle_models.id", ondelete="NO ACTION"),
            nullable=True,
        ),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "branch_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("vehicle_branches.id", ondelete="NO ACTION"),
            nullable=True,
        ),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "color_id", sa.Uuid(as_uuid=True), sa.ForeignKey("vehicle_colors.id", ondelete="NO ACTION"), nullable=True
        ),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "keys_option_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("vehicle_key_options.id", ondelete="NO ACTION"),
            nullable=True,
        ),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "fuel_type_id", sa.Uuid(as_uuid=True), sa.ForeignKey("fuel_types.id", ondelete="NO ACTION"), nullable=True
        ),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "bidding_model_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("bidding_models.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("vehicle_listings", sa.Column("year", sa.Integer(), nullable=True))
    op.add_column("vehicle_listings", sa.Column("target_selling_price", sa.Numeric(12, 2), nullable=True))
    op.add_column("vehicle_listings", sa.Column("minimum_selling_price", sa.Numeric(12, 2), nullable=True))
    op.add_column("vehicle_listings", sa.Column("previous_number_plate", sa.String(length=50), nullable=True))
    # NO ACTION (not SET NULL): SQL Server rejects a second SET NULL cascade
    # path into `users` alongside seller_id's existing one (see models/content.py).
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "sub_seller_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
        ),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "created_by_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
        ),
    )
    op.add_column("vehicle_listings", sa.Column("mulkhiya_document_url", sa.String(length=500), nullable=True))
    op.add_column(
        "vehicle_listings",
        sa.Column("terms_accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "vehicle_listings",
        sa.Column("status", sa.String(length=30), nullable=False, server_default="submitted"),
    )

    # Every row that exists at migration time predates the intake form and is
    # already a live/curated listing - only newly-submitted rows should carry
    # the "submitted" default going forward.
    op.execute("UPDATE vehicle_listings SET status = 'published'")


def downgrade() -> None:
    op.drop_column("vehicle_listings", "status")
    op.drop_column("vehicle_listings", "terms_accepted")
    op.drop_column("vehicle_listings", "mulkhiya_document_url")
    op.drop_column("vehicle_listings", "created_by_id")
    op.drop_column("vehicle_listings", "sub_seller_id")
    op.drop_column("vehicle_listings", "previous_number_plate")
    op.drop_column("vehicle_listings", "minimum_selling_price")
    op.drop_column("vehicle_listings", "target_selling_price")
    op.drop_column("vehicle_listings", "year")
    op.drop_column("vehicle_listings", "bidding_model_id")
    op.drop_column("vehicle_listings", "fuel_type_id")
    op.drop_column("vehicle_listings", "keys_option_id")
    op.drop_column("vehicle_listings", "color_id")
    op.drop_column("vehicle_listings", "branch_id")
    op.drop_column("vehicle_listings", "model_id")
    op.drop_column("vehicle_listings", "make_id")
    op.execute("DROP INDEX ix_vehicle_listings_chassis_number ON vehicle_listings")
    op.drop_column("vehicle_listings", "chassis_number")
