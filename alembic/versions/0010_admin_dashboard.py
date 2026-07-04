"""admin sidebar nav items and dashboard action cards

Revision ID: 0010_admin_dashboard
Revises: 0009_vehicle_seller_bid_fk
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_admin_dashboard"
down_revision: str | None = "0009_vehicle_seller_bid_fk"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def upgrade() -> None:
    op.create_table(
        "admin_nav_items",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("label_en", sa.Unicode(length=100), nullable=False),
        sa.Column("label_ar", sa.Unicode(length=100), nullable=False),
        sa.Column("icon_class", sa.String(length=100), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "admin_dashboard_cards",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("section_key", sa.String(length=50), nullable=False),
        sa.Column("label_en", sa.Unicode(length=150), nullable=False),
        sa.Column("label_ar", sa.Unicode(length=150), nullable=False),
        sa.Column("description_en", sa.Unicode(length=300), nullable=True),
        sa.Column("description_ar", sa.Unicode(length=300), nullable=True),
        sa.Column("icon_class", sa.String(length=100), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_admin_dashboard_cards_section_key", "admin_dashboard_cards", ["section_key"])

    _seed_nav_items()
    _seed_dashboard_cards()

    op.alter_column("admin_nav_items", "sort_order", server_default=None)
    op.alter_column("admin_nav_items", "is_active", server_default=None)
    op.alter_column("admin_dashboard_cards", "sort_order", server_default=None)
    op.alter_column("admin_dashboard_cards", "is_active", server_default=None)


def _seed_nav_items() -> None:
    nav_items = sa.table(
        "admin_nav_items",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("label_en", sa.Unicode(length=100)),
        sa.column("label_ar", sa.Unicode(length=100)),
        sa.column("icon_class", sa.String(length=100)),
        sa.column("url", sa.String(length=500)),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        nav_items,
        [
            {
                "id": _uuid(),
                "label_en": "Home",
                "label_ar": "الرئيسية",
                "icon_class": "fa-solid fa-house",
                "url": "/",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "label_en": "Sellers",
                "label_ar": "البائعون",
                "icon_class": "fa-solid fa-user-tag",
                "url": "/admin/sellers",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "label_en": "Operations",
                "label_ar": "العمليات",
                "icon_class": "fa-solid fa-gears",
                "url": "/admin/operations",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "label_en": "Management",
                "label_ar": "الإدارة",
                "icon_class": "fa-solid fa-users-gear",
                "url": "/admin/management",
                "sort_order": 4,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "label_en": "Accountant",
                "label_ar": "المحاسبة",
                "icon_class": "fa-solid fa-file-invoice-dollar",
                "url": "/admin/accountant",
                "sort_order": 5,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "label_en": "Reports",
                "label_ar": "التقارير",
                "icon_class": "fa-solid fa-chart-column",
                "url": "/admin/reports",
                "sort_order": 6,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "label_en": "Admin",
                "label_ar": "الإدارة العامة",
                "icon_class": "fa-solid fa-user-shield",
                "url": "/admin",
                "sort_order": 7,
                "is_active": True,
            },
        ],
    )


def _seed_dashboard_cards() -> None:
    cards = sa.table(
        "admin_dashboard_cards",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("section_key", sa.String(length=50)),
        sa.column("label_en", sa.Unicode(length=150)),
        sa.column("label_ar", sa.Unicode(length=150)),
        sa.column("description_en", sa.Unicode(length=300)),
        sa.column("description_ar", sa.Unicode(length=300)),
        sa.column("icon_class", sa.String(length=100)),
        sa.column("url", sa.String(length=500)),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )

    dashboard_section = [
        {
            "label_en": "Auctions",
            "label_ar": "المزادات",
            "description_en": "Review live, scheduled, and closed auctions.",
            "description_ar": "مراجعة المزادات المباشرة والمجدولة والمغلقة.",
            "icon_class": "fa-solid fa-gavel",
            "url": "/admin/auctions",
        },
        {
            "label_en": "Users",
            "label_ar": "المستخدمون",
            "description_en": "Manage buyer and seller accounts.",
            "description_ar": "إدارة حسابات المشترين والبائعين.",
            "icon_class": "fa-solid fa-users",
            "url": "/admin/users",
        },
    ]

    sellers_section = [
        {
            "label_en": "Add a New Car",
            "label_ar": "إضافة سيارة جديدة",
            "description_en": "List a new vehicle for sale or auction.",
            "description_ar": "إدراج مركبة جديدة للبيع أو المزاد.",
            "icon_class": "fa-solid fa-car",
            "url": "/admin/sellers/add-a-new-car",
        },
        {
            "label_en": "My Vehicles",
            "label_ar": "مركباتي",
            "description_en": "View and manage all vehicles you've listed.",
            "description_ar": "عرض وإدارة جميع المركبات التي أدرجتها.",
            "icon_class": "fa-solid fa-car-side",
            "url": "/admin/sellers/my-vehicles",
        },
        {
            "label_en": "My Received Vehicles",
            "label_ar": "المركبات المستلمة",
            "description_en": "Vehicles received and pending processing.",
            "description_ar": "المركبات المستلمة والمعلقة قيد المعالجة.",
            "icon_class": "fa-solid fa-truck-ramp-box",
            "url": "/admin/sellers/my-received-vehicles",
        },
        {
            "label_en": "Active Auctions",
            "label_ar": "المزادات النشطة",
            "description_en": "Auctions currently open for bidding.",
            "description_ar": "المزادات المفتوحة حاليًا للمزايدة.",
            "icon_class": "fa-solid fa-gavel",
            "url": "/admin/sellers/active-auctions",
        },
        {
            "label_en": "Sold Undelivered",
            "label_ar": "مباعة وغير مسلمة",
            "description_en": "Sold vehicles awaiting delivery.",
            "description_ar": "المركبات المباعة بانتظار التسليم.",
            "icon_class": "fa-solid fa-box-open",
            "url": "/admin/sellers/sold-undelivered",
        },
        {
            "label_en": "Unsold Vehicles Undelivered",
            "label_ar": "غير مباعة وغير مسلمة",
            "description_en": "Unsold vehicles still awaiting return delivery.",
            "description_ar": "المركبات غير المباعة التي لا تزال بانتظار إعادة التسليم.",
            "icon_class": "fa-solid fa-triangle-exclamation",
            "url": "/admin/sellers/unsold-vehicles-undelivered",
        },
        {
            "label_en": "My Invoices",
            "label_ar": "فواتيري",
            "description_en": "View invoices issued to your account.",
            "description_ar": "عرض الفواتير الصادرة لحسابك.",
            "icon_class": "fa-solid fa-file-invoice",
            "url": "/admin/sellers/my-invoices",
        },
        {
            "label_en": "My Payments",
            "label_ar": "مدفوعاتي",
            "description_en": "Track payments received and outstanding.",
            "description_ar": "تتبع المدفوعات المستلمة والمستحقة.",
            "icon_class": "fa-solid fa-wallet",
            "url": "/admin/sellers/my-payments",
        },
        {
            "label_en": "Requested Services",
            "label_ar": "الخدمات المطلوبة",
            "description_en": "Services you've requested for your vehicles.",
            "description_ar": "الخدمات التي طلبتها لمركباتك.",
            "icon_class": "fa-solid fa-clipboard-list",
            "url": "/admin/sellers/requested-services",
        },
        {
            "label_en": "Completed Requests",
            "label_ar": "الطلبات المكتملة",
            "description_en": "Service requests that have been completed.",
            "description_ar": "طلبات الخدمة التي تم إنجازها.",
            "icon_class": "fa-solid fa-circle-check",
            "url": "/admin/sellers/completed-requests",
        },
        {
            "label_en": "Unapproved Vehicle",
            "label_ar": "مركبة غير معتمدة",
            "description_en": "Vehicles pending approval before listing.",
            "description_ar": "المركبات بانتظار الموافقة قبل الإدراج.",
            "icon_class": "fa-solid fa-car-burst",
            "url": "/admin/sellers/unapproved-vehicle",
        },
    ]

    rows = []
    for sort_order, card in enumerate(dashboard_section, start=1):
        rows.append({"id": _uuid(), "section_key": "dashboard", "sort_order": sort_order, "is_active": True, **card})
    for sort_order, card in enumerate(sellers_section, start=1):
        rows.append({"id": _uuid(), "section_key": "sellers", "sort_order": sort_order, "is_active": True, **card})

    op.bulk_insert(cards, rows)


def downgrade() -> None:
    op.drop_index("ix_admin_dashboard_cards_section_key", table_name="admin_dashboard_cards")
    op.drop_table("admin_dashboard_cards")
    op.drop_table("admin_nav_items")
