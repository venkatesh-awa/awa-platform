"""seed admin dashboard cards for the management section

Revision ID: 0013_admin_management_cards
Revises: 0012_admin_operations_cards
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from urllib.parse import quote

import sqlalchemy as sa

from alembic import op

revision: str = "0013_admin_management_cards"
down_revision: str | None = "0012_admin_operations_cards"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_IMAGE_BASE = "https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _image(filename: str) -> str:
    return _IMAGE_BASE + quote(filename)


# (slug, label_en, label_ar, image filename) - label/image sourced straight
# from the UAT management page markup (p tag text + img src); label_ar is a
# direct Arabic translation of label_en.
_MANAGEMENT_CARDS: list[tuple[str, str, str, str]] = [
    ("active-auctions", "Active Auctions", "المزادات النشطة", "Active auction.svg"),
    ("sales-invoice-details", "Sales Invoice Details", "تفاصيل فاتورة المبيعات", "Sales invoice details.svg"),
    ("sellers-report", "Sellers Report", "تقرير البائعين", "Sales report.svg"),
    ("sales-report", "Sales Report", "تقرير المبيعات", "Sales report.svg"),
    ("auction-list", "Auction List", "قائمة المزادات", "seller report.svg"),
    ("customers-list", "Customer List", "قائمة العملاء", "Customer list.svg"),
    ("auction-batch-list", "Auction Batch List", "قائمة دفعات المزاد", "Auction Batch List.svg"),
    ("sellers-list", "Seller List", "قائمة البائعين", "Seller list.svg"),
    ("income-totals", "Income Totals", "إجمالي الدخل", "income total.svg"),
    ("monthly-income-totals", "Monthly Income Totals", "إجمالي الدخل الشهري", "monthly income totals.svg"),
    ("employees-permission", "Employees Permission", "صلاحيات الموظفين", "permissions.svg"),
    ("penalty-management", "Penalty Management", "إدارة الغرامات", "Auction Batch List.svg"),
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
                "section_key": "management",
                "label_en": label_en,
                "label_ar": label_ar,
                "url": f"/admin/management/{slug}",
                "image_url": _image(image_filename),
                "sort_order": sort_order,
                "is_active": True,
            }
            for sort_order, (slug, label_en, label_ar, image_filename) in enumerate(_MANAGEMENT_CARDS, start=1)
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM admin_dashboard_cards WHERE section_key = 'management'"))
