"""seed real sub-sellers from the live Al Wataneya admin module's
sub-seller list, so the "Add a New Car" form's Sub Seller field has real
data once its Client is selected.

Revision ID: 0023_seed_sub_sellers
Revises: 0022_sub_sellers
Create Date: 2026-07-05

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0023_seed_sub_sellers"
down_revision: str | None = "0022_sub_sellers"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# (external_id, seller_id (parent client's user_id), name, phone) - verbatim
# from the admin module's sub-seller list.
_SUB_SELLERS: list[tuple[str, str, str, str]] = [
    ("1057", "9e309d19-1acf-4e7b-a824-706b0f902e46", "Anuritha 1", "+876098123"),
    ("1056", "9e309d19-1acf-4e7b-a824-706b0f902e46", "Anuritha J", "+876209734"),
]


def upgrade() -> None:
    bind = op.get_bind()
    insert_sql = sa.text(
        """
        INSERT INTO sub_sellers (id, seller_id, name, phone, external_id, is_active)
        SELECT :id, :seller_id, :name, :phone, :external_id, 1
        WHERE NOT EXISTS (SELECT 1 FROM sub_sellers WHERE external_id = :external_id)
          AND EXISTS (SELECT 1 FROM users WHERE id = :seller_id)
        """
    )
    for external_id, seller_id, name, phone in _SUB_SELLERS:
        bind.execute(
            insert_sql,
            {
                "id": str(uuid.uuid4()),
                "seller_id": seller_id,
                "name": name,
                "phone": phone,
                "external_id": external_id,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    delete_sql = sa.text("DELETE FROM sub_sellers WHERE external_id = :external_id")
    for external_id, _seller_id, _name, _phone in _SUB_SELLERS:
        bind.execute(delete_sql, {"external_id": external_id})
