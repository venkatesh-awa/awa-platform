"""replace legacy home menu URL

Revision ID: 0027_home_menu_url
Revises: 0026_admin_menu_icon_null
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0027_home_menu_url"
down_revision: str | None = "0026_admin_menu_icon_null"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE menu_items
            SET url = '/'
            WHERE url = '/seller-buyer/home'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE menu_items
            SET url = '/seller-buyer/home'
            WHERE url = '/'
              AND label_en = 'Home'
            """
        )
    )
