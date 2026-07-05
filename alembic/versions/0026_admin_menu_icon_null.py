"""clear admin menu icon and ensure labels

Revision ID: 0026_admin_menu_icon_null
Revises: 0025_seller_card_icons_null
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026_admin_menu_icon_null"
down_revision: str | None = "0025_seller_card_icons_null"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE admin_nav_items
            SET label_en = N'Admin',
                label_ar = N'الإدارة العامة',
                icon_class = NULL
            WHERE url = '/admin'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE admin_nav_items
            SET label_en = N'Admin',
                label_ar = N'الإدارة العامة',
                icon_class = 'fa-solid fa-user-shield'
            WHERE url = '/admin'
            """
        )
    )
