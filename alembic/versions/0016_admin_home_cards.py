"""seed admin dashboard cards for the admin (top-level) section

Revision ID: 0016_admin_home_cards
Revises: 0015_admin_reports_cards
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from urllib.parse import quote

import sqlalchemy as sa

from alembic import op

revision: str = "0016_admin_home_cards"
down_revision: str | None = "0015_admin_reports_cards"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_IMAGE_BASE = "https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _image(filename: str) -> str:
    return _IMAGE_BASE + quote(filename)


# (slug, label_en, label_ar, image filename) - label/image sourced straight
# from the UAT admin page markup (p tag text + img src); label_ar is a direct
# Arabic translation of label_en. Several of these overlap in concept with
# the existing "dashboard" section cards (0011) - reuse the same Arabic
# wording there for consistency.
_ADMIN_CARDS: list[tuple[str, str, str, str]] = [
    ("service-list", "Service List", "قائمة الخدمة", "service.png"),
    ("expense-list", "Expense List", "قائمة المصروفات", "Expense List.svg"),
    ("features-list", "Features Management", "إدارة الميزات", "features.svg"),
    ("make-model", "Makes and Models Management", "إدارة الماركات والموديلات", "Makes Models.svg"),
    ("locations", "Location List", "قائمة المواقع", "my-invoices.svg"),
    ("services", "Services List", "قائمة الخدمات", "service.png"),
    ("message-templates", "Message Templates", "قوالب الرسائل", "Message Templates.svg"),
    ("auction-groups", "Auction Groups", "مجموعات المزادات", "totalcustomer.svg"),
    ("inspection-packages", "Inspection Packages", "باقات الفحص", "Expense List.svg"),
    ("compliance-details", "Complaint Details", "تفاصيل الشكاوى", "Expense List.svg"),
]


def upgrade() -> None:
    cards = sa.table(
        "admin_dashboard_cards",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("section_key", sa.String(length=50)),
        sa.column("label_en", sa.Unicode(length=150)),
        sa.column("label_ar", sa.Unicode(length=150)),
        sa.column("url", sa.String(length=500)),
        sa.column("image_url", sa.String(length=500)),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        cards,
        [
            {
                "id": _uuid(),
                "section_key": "admin",
                "label_en": label_en,
                "label_ar": label_ar,
                "url": f"/admin/{slug}",
                "image_url": _image(image_filename),
                "sort_order": sort_order,
                "is_active": True,
            }
            for sort_order, (slug, label_en, label_ar, image_filename) in enumerate(_ADMIN_CARDS, start=1)
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM admin_dashboard_cards WHERE section_key = 'admin'"))
