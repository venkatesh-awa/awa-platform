"""add UAT image URLs for seller dashboard cards

Revision ID: 0024_seller_card_images
Revises: 0023_seed_sub_sellers
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import quote

import sqlalchemy as sa

from alembic import op

revision: str = "0024_seller_card_images"
down_revision: str | None = "0023_seed_sub_sellers"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_IMAGE_BASE = "https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/"


def _image(filename: str) -> str:
    return _IMAGE_BASE + quote(filename)


# (existing local card URL, image filename) sourced from the UAT sellers
# dashboard markup.
_SELLER_CARD_IMAGES: list[tuple[str, str]] = [
    ("/admin/sellers/add-a-new-car", "add-new-car.svg"),
    ("/admin/sellers/my-vehicles", "my-vehicles.svg"),
    ("/admin/sellers/my-received-vehicles", "my-received-vehicles.svg"),
    ("/admin/sellers/active-auctions", "liveauction.svg"),
    ("/admin/sellers/sold-undelivered", "sold-vehicles.svg"),
    ("/admin/sellers/unsold-vehicles-undelivered", "unsold-vehicles.svg"),
    ("/admin/sellers/my-invoices", "my-invoices.svg"),
    ("/admin/sellers/my-payments", "my-payments.svg"),
    ("/admin/sellers/requested-services", "report.png"),
    ("/admin/sellers/completed-requests", "completed-requests.svg"),
    ("/admin/sellers/unapproved-vehicle", "under-approval.svg"),
]


def upgrade() -> None:
    bind = op.get_bind()
    update_sql = sa.text(
        """
        UPDATE admin_dashboard_cards
        SET image_url = :image_url
        WHERE section_key = 'sellers'
          AND url = :url
        """
    )
    for url, image_filename in _SELLER_CARD_IMAGES:
        bind.execute(update_sql, {"url": url, "image_url": _image(image_filename)})


def downgrade() -> None:
    bind = op.get_bind()
    clear_sql = sa.text(
        """
        UPDATE admin_dashboard_cards
        SET image_url = NULL
        WHERE section_key = 'sellers'
          AND url = :url
        """
    )
    for url, _image_filename in _SELLER_CARD_IMAGES:
        bind.execute(clear_sql, {"url": url})
