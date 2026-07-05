"""clear admin icon from public menu items

Revision ID: 0028_menu_admin_icon_null
Revises: 0027_home_menu_url
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0028_menu_admin_icon_null"
down_revision: str | None = "0027_home_menu_url"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE menu_items
            SET icon_class = NULL
            WHERE icon_class = 'fa-solid fa-user-shield'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE menu_items
            SET icon_class = 'fa-solid fa-user-shield'
            WHERE label_en = 'Admin'
              AND url = '#'
              AND icon_class IS NULL
            """
        )
    )
