"""clear seller dashboard card icon classes

Revision ID: 0025_seller_card_icons_null
Revises: 0024_seller_card_images
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0025_seller_card_icons_null"
down_revision: str | None = "0024_seller_card_images"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_SELLER_ICON_CLASSES: dict[str, str] = {
    "/admin/sellers/add-a-new-car": "fa-solid fa-car",
    "/admin/sellers/my-vehicles": "fa-solid fa-car-side",
    "/admin/sellers/my-received-vehicles": "fa-solid fa-truck-ramp-box",
    "/admin/sellers/active-auctions": "fa-solid fa-gavel",
    "/admin/sellers/sold-undelivered": "fa-solid fa-box-open",
    "/admin/sellers/unsold-vehicles-undelivered": "fa-solid fa-triangle-exclamation",
    "/admin/sellers/my-invoices": "fa-solid fa-file-invoice",
    "/admin/sellers/my-payments": "fa-solid fa-wallet",
    "/admin/sellers/requested-services": "fa-solid fa-clipboard-list",
    "/admin/sellers/completed-requests": "fa-solid fa-circle-check",
    "/admin/sellers/unapproved-vehicle": "fa-solid fa-car-burst",
}


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE admin_dashboard_cards
            SET icon_class = NULL
            WHERE section_key = 'sellers'
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    update_sql = sa.text(
        """
        UPDATE admin_dashboard_cards
        SET icon_class = :icon_class
        WHERE section_key = 'sellers'
          AND url = :url
        """
    )
    for url, icon_class in _SELLER_ICON_CLASSES.items():
        bind.execute(update_sql, {"url": url, "icon_class": icon_class})
