"""seed admin dashboard cards for the operations section

Revision ID: 0012_admin_operations_cards
Revises: 0011_admin_dashboard_submenus
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from urllib.parse import quote

import sqlalchemy as sa

from alembic import op

revision: str = "0012_admin_operations_cards"
down_revision: str | None = "0011_admin_dashboard_submenus"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_IMAGE_BASE = "https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _image(filename: str) -> str:
    return _IMAGE_BASE + quote(filename)


# (slug, label_en, label_ar, image filename) - label/image sourced straight
# from the UAT operations page markup (p tag text + img src); label_ar is a
# direct Arabic translation of label_en.
_OPERATIONS_CARDS: list[tuple[str, str, str, str]] = [
    ("addnew-car", "Add a New Car", "إضافة سيارة جديدة", "add-new-car.svg"),
    ("add-new-car-from-erp", "Request Vehicle from ERP", "طلب مركبة من نظام ERP", "add-new-car.svg"),
    ("request-vehicle", "Request Vehicle", "طلب مركبة", "request vehicle.svg"),
    ("washed-vehicle", "Washed Vehicle", "مركبة مغسولة", "Washed vehicle.svg"),
    ("photo-vehicle", "Photo Vehicle", "تصوير المركبة", "photo vehicle.svg"),
    ("technical-test", "Technical Test", "الفحص الفني", "tecnical report.svg"),
    ("submitted-by-seller", "Submitted by Seller", "مقدمة من البائع", "submit by seller.svg"),
    ("inactive-auctions", "Inactive Auctions", "المزادات غير النشطة", "inactive auction.svg"),
    ("active-auctionn", "Active Auctions", "المزادات النشطة", "Active auction.svg"),
    ("awarded-report", "Awarded Report", "تقرير الترسية", "awarded report.svg"),
    ("approved-by-seller", "Approved by Seller", "معتمدة من البائع", "Approved by seller.svg"),
    ("underapproval", "Under Approval", "قيد الموافقة", "under approval.svg"),
    ("sold-vehicle", "Sold Undelivered", "مباعة وغير مسلمة", "sold undelivered.svg"),
    ("buyer-change", "Buyer Change", "تغيير المشتري", "buyer change.svg"),
    ("completed-bch-services", "Completed B.Ch Services", "خدمات B.Ch المكتملة", "Completed B.Ch Services.svg"),
    ("car-inspection-services", "Car Inspection Services", "خدمات فحص السيارة", "Car inspection services.svg"),
    ("unsold-vehicle", "Unsold", "غير مباعة", "unsold-1.svg"),
    (
        "completed-inspection-services",
        "Completed Inspection Services",
        "خدمات الفحص المكتملة",
        "Completed Inspection Services.svg",
    ),
    ("sold-delivered", "Sold Delivered", "مباعة ومسلمة", "sold delivered.svg"),
    ("get-archived-list", "Archived Vehicle", "مركبة مؤرشفة", "Archived vehicle.svg"),
    ("marketing", "Marketing", "التسويق", "marketing.svg"),
    ("pending_services", "Pending Services", "الخدمات المعلقة", "pending servies.svg"),
    ("services-in-process", "Services in Process", "الخدمات قيد التنفيذ", "Services in progress.svg"),
    ("completed-requests", "Completed Requests", "الطلبات المكتملة", "Completed services.svg"),
    ("sp-requested-services", "SP Requested Services", "الخدمات المطلوبة من مزود الخدمة", "report.png"),
    ("completed-sp-services", "Completed SP Services", "خدمات مزود الخدمة المكتملة", "report.png"),
    ("operations-logs", "Operation Log", "سجل العمليات", "log.png"),
    ("under-approval-direct-sales", "Under Approval Direct Sales", "البيع المباشر قيد الموافقة", "attestation.png"),
    ("center-manager", "Center Manager", "مدير المركز", "awarded report.svg"),
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
                "section_key": "operations",
                "label_en": label_en,
                "label_ar": label_ar,
                "url": f"/admin/operations/{slug}",
                "image_url": _image(image_filename),
                "sort_order": sort_order,
                "is_active": True,
            }
            for sort_order, (slug, label_en, label_ar, image_filename) in enumerate(_OPERATIONS_CARDS, start=1)
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM admin_dashboard_cards WHERE section_key = 'operations'"))
