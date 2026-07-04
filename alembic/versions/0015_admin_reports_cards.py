"""seed admin dashboard cards for the reports section

Revision ID: 0015_admin_reports_cards
Revises: 0014_admin_accountant_cards
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from urllib.parse import quote

import sqlalchemy as sa

from alembic import op

revision: str = "0015_admin_reports_cards"
down_revision: str | None = "0014_admin_accountant_cards"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_IMAGE_BASE = "https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _image(filename: str) -> str:
    return _IMAGE_BASE + quote(filename)


# (slug, label_en, label_ar, image filename) - label/image sourced straight
# from the UAT reports page markup (p tag text + img src, data-url in place of
# href since these cards call openReport(this) client-side); label_ar is a
# direct Arabic translation of label_en.
_REPORTS_CARDS: list[tuple[str, str, str, str]] = [
    ("statistical-report", "Statistical Report", "التقرير الإحصائي", "Statical Report.svg"),
    ("sales-report", "Sales Report", "تقرير المبيعات", "Sales report.svg"),
    ("sales-report-by-features", "Sales Report by Features", "تقرير المبيعات حسب الميزات", "Sales Report By Features.svg"),
    ("active-auction", "Active Auctions", "المزادات النشطة", "Active auction.svg"),
    ("auction-end", "Auction End", "انتهاء المزاد", "Auction end.svg"),
    ("car-price-report", "Car Price Report", "تقرير أسعار السيارات", "Car inspection report.svg"),
    ("feature-car-price-report", "Feature Car Price Report", "تقرير أسعار السيارات المميزة", "Feature car price report.svg"),
    ("delivered-vehicles", "Delivered Vehicles", "المركبات المسلمة", "Feature car price report.svg"),
    ("auction-reports", "Auction Reports", "تقارير المزادات", "Feature car price report.svg"),
    ("vehicle-management", "Vehicle Management", "إدارة المركبات", "Feature car price report.svg"),
    ("buyer-reports", "Buyer Report", "تقرير المشتري", "Feature car price report.svg"),
    ("sellers-reports", "Seller Report", "تقرير البائع", "Feature car price report.svg"),
    ("other-reports", "Other Reports", "تقارير أخرى", "Feature car price report.svg"),
    ("brand-performance-report", "Brand Performance Report", "تقرير أداء العلامة التجارية", "Feature car price report.svg"),
    ("inspection-reports", "Inspection Reports", "تقارير الفحص", "Feature car price report.svg"),
    ("approval-creation", "Approval Creation", "إنشاء الموافقة", "Feature car price report.svg"),
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
                "section_key": "reports",
                "label_en": label_en,
                "label_ar": label_ar,
                "url": f"/admin/reports/{slug}",
                "image_url": _image(image_filename),
                "sort_order": sort_order,
                "is_active": True,
            }
            for sort_order, (slug, label_en, label_ar, image_filename) in enumerate(_REPORTS_CARDS, start=1)
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM admin_dashboard_cards WHERE section_key = 'reports'"))
