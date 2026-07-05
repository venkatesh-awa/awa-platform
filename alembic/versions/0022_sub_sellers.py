"""create sub_sellers (a seller's named contacts - id/name/phone, not a full
account) and repoint vehicle_listings.sub_seller_id at it instead of users.

The "Add a New Car" form's Sub Seller field was originally modeled as
another `users` row scoped by a self-referencing parent_seller_id (see the
now-removed 0022/0023 draft), but the real admin module's sub-seller data
(GET .../sub-sellers) has no email/login - just an id, a name, a phone
number, and the parent seller's user id. This migration replaces that
draft with the correct shape.

vehicle_listings.sub_seller_id has never held real data (submissions only
went live after this feature existed), so it's safe to drop and recreate
the column rather than attempt an in-place FK retarget.

Revision ID: 0022_sub_sellers
Revises: 0021_seed_uat_seller_users
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022_sub_sellers"
down_revision: str | None = "0021_seed_uat_seller_users"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# SQL Server auto-names FK constraints (e.g. "FK__vehicle_l__sub_s__5F492382"),
# so the existing constraint on vehicle_listings.sub_seller_id can't be
# hardcoded here - look it up and drop it dynamically instead.
_DROP_EXISTING_FK_SQL = """
DECLARE @constraint_name NVARCHAR(200);
SELECT @constraint_name = fk.name
FROM sys.foreign_keys fk
JOIN sys.tables t ON fk.parent_object_id = t.object_id
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.columns c ON c.object_id = t.object_id AND c.column_id = fkc.parent_column_id
WHERE t.name = 'vehicle_listings' AND c.name = 'sub_seller_id';

IF @constraint_name IS NOT NULL
BEGIN
    DECLARE @sql NVARCHAR(500) = 'ALTER TABLE vehicle_listings DROP CONSTRAINT ' + @constraint_name;
    EXEC sp_executesql @sql;
END
"""


def upgrade() -> None:
    op.create_table(
        "sub_sellers",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("seller_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"),
                   nullable=False, index=True),
        sa.Column("name", sa.Unicode(length=150), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("external_id", sa.String(length=50), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
    )

    op.execute(_DROP_EXISTING_FK_SQL)
    op.drop_column("vehicle_listings", "sub_seller_id")
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "sub_seller_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("sub_sellers.id", ondelete="NO ACTION"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.execute(_DROP_EXISTING_FK_SQL)
    op.drop_column("vehicle_listings", "sub_seller_id")
    op.add_column(
        "vehicle_listings",
        sa.Column(
            "sub_seller_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
        ),
    )
    op.drop_table("sub_sellers")
