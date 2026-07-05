"""add users.parent_seller_id so the "Add a New Car" form's Sub Seller field
can be scoped to whichever Client (seller) is selected, instead of searching
all sellers independently.

Revision ID: 0022_user_parent_seller
Revises: 0021_seed_uat_seller_users
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022_user_parent_seller"
down_revision: str | None = "0021_seed_uat_seller_users"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "parent_seller_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="NO ACTION"),
            nullable=True,
        ),
    )
    op.create_index("ix_users_parent_seller_id", "users", ["parent_seller_id"])


def downgrade() -> None:
    op.drop_index("ix_users_parent_seller_id", table_name="users")
    op.drop_column("users", "parent_seller_id")
