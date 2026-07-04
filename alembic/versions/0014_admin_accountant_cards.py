"""seed admin dashboard cards for the accountant section

Revision ID: 0014_admin_accountant_cards
Revises: 0013_admin_management_cards
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from urllib.parse import quote

import sqlalchemy as sa

from alembic import op

revision: str = "0014_admin_accountant_cards"
down_revision: str | None = "0013_admin_management_cards"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_IMAGE_BASE = "https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _image(filename: str) -> str:
    return _IMAGE_BASE + quote(filename)


# (slug, label_en, label_ar, image filename) - label/image sourced straight
# from the UAT accountant page markup (p tag text + img src); label_ar is a
# direct Arabic translation of label_en.
_ACCOUNTANT_CARDS: list[tuple[str, str, str, str]] = [
    ("Sold-Vehicles", "Sold Undelivered", "مباعة وغير مسلمة", "sold undelivered.svg"),
    ("car-inspection-invoices", "Car Inspection Invoices", "فواتير فحص السيارة", "Car inspection services.svg"),
    ("buyer-change-invoices", "Buyer Change Invoices", "فواتير تغيير المشتري", "Buyer change incvoice.svg"),
    ("seller-invoice-list", "Seller Invoice List", "قائمة فواتير البائع", "Seller invoice list.svg"),
    ("buyer-invoice-list", "Buyer Invoice List", "قائمة فواتير المشتري", "Buyer invoice list.svg"),
    ("seller-payments", "Seller Payments", "مدفوعات البائع", "Seller payments.svg"),
    ("buyer-payments", "Buyer Payments", "مدفوعات المشتري", "Buyer payments.svg"),
    ("customer", "Customers", "العملاء", "Customers.svg"),
    ("security-deposit", "Security Deposit", "الوديعة الضمانية", "Security deposits.svg"),
    ("seller-invoices-list", "Seller Invoice List", "قائمة فواتير البائع", "Seller invoice list.svg"),
    ("fines-penalties", "Fines and Penalties", "الغرامات والعقوبات", "Seller invoice list.svg"),
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
                "section_key": "accountant",
                "label_en": label_en,
                "label_ar": label_ar,
                "url": f"/admin/accountant/{slug}",
                "image_url": _image(image_filename),
                "sort_order": sort_order,
                "is_active": True,
            }
            for sort_order, (slug, label_en, label_ar, image_filename) in enumerate(_ACCOUNTANT_CARDS, start=1)
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM admin_dashboard_cards WHERE section_key = 'accountant'"))
