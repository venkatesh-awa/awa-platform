"""admin nav nesting (Admin -> Dashboard, In Store) and real dashboard cards

Revision ID: 0011_admin_dashboard_submenus
Revises: 0010_admin_dashboard
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_admin_dashboard_submenus"
down_revision: str | None = "0010_admin_dashboard"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def upgrade() -> None:
    op.add_column("admin_nav_items", sa.Column("parent_id", sa.Uuid(as_uuid=True), nullable=True))
    op.create_index("ix_admin_nav_items_parent_id", "admin_nav_items", ["parent_id"])
    op.create_foreign_key(
        "fk_admin_nav_items_parent_id",
        "admin_nav_items",
        "admin_nav_items",
        ["parent_id"],
        ["id"],
        ondelete="NO ACTION",
    )

    connection = op.get_bind()
    admin_id = connection.execute(
        sa.text("SELECT id FROM admin_nav_items WHERE label_en = 'Admin'")
    ).scalar_one()

    nav_items = sa.table(
        "admin_nav_items",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("parent_id", sa.Uuid(as_uuid=True)),
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
                "parent_id": admin_id,
                "label_en": "Dashboard",
                "label_ar": "لوحة التحكم",
                "icon_class": None,
                "url": "/admin/dashboard",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "parent_id": admin_id,
                "label_en": "In Store",
                "label_ar": "داخل المتجر",
                "icon_class": None,
                "url": "/admin/instore",
                "sort_order": 2,
                "is_active": True,
            },
        ],
    )

    # Replace the earlier placeholder "dashboard" cards (Auctions/Users - a
    # guess made before seeing the real UAT design) with the real grid.
    connection.execute(sa.text("DELETE FROM admin_dashboard_cards WHERE section_key = 'dashboard'"))

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
    dashboard_cards = [
        {
            "label_en": "Location List",
            "label_ar": "قائمة المواقع",
            "description_en": "Manage branch and yard locations.",
            "description_ar": "إدارة مواقع الفروع والساحات.",
            "icon_class": "fa-solid fa-location-dot",
            "url": "/admin/dashboard/location-list",
        },
        {
            "label_en": "Services List",
            "label_ar": "قائمة الخدمات",
            "description_en": "Manage the value-added services offered to sellers.",
            "description_ar": "إدارة الخدمات ذات القيمة المضافة المقدمة للبائعين.",
            "icon_class": "fa-solid fa-hand-holding-dollar",
            "url": "/admin/dashboard/services-list",
        },
        {
            "label_en": "Message Templates",
            "label_ar": "قوالب الرسائل",
            "description_en": "Manage notification and email message templates.",
            "description_ar": "إدارة قوالب رسائل الإشعارات والبريد الإلكتروني.",
            "icon_class": "fa-solid fa-comment-dots",
            "url": "/admin/dashboard/message-templates",
        },
        {
            "label_en": "Auction Groups",
            "label_ar": "مجموعات المزادات",
            "description_en": "Manage groupings used to organize auctions.",
            "description_ar": "إدارة التجميعات المستخدمة لتنظيم المزادات.",
            "icon_class": "fa-solid fa-layer-group",
            "url": "/admin/dashboard/auction-groups",
        },
        {
            "label_en": "Inspection Packages",
            "label_ar": "باقات الفحص",
            "description_en": "Manage vehicle inspection package offerings.",
            "description_ar": "إدارة باقات فحص المركبات المقدمة.",
            "icon_class": "fa-solid fa-clipboard-check",
            "url": "/admin/dashboard/inspection-packages",
        },
        {
            "label_en": "Complaint Details",
            "label_ar": "تفاصيل الشكاوى",
            "description_en": "Review and manage submitted complaints.",
            "description_ar": "مراجعة وإدارة الشكاوى المقدمة.",
            "icon_class": "fa-solid fa-triangle-exclamation",
            "url": "/admin/dashboard/complaint-details",
        },
    ]
    op.bulk_insert(
        cards,
        [
            {"id": _uuid(), "section_key": "dashboard", "sort_order": sort_order, "is_active": True, **card}
            for sort_order, card in enumerate(dashboard_cards, start=1)
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM admin_dashboard_cards WHERE section_key = 'dashboard'"))
    op.execute(sa.text("DELETE FROM admin_nav_items WHERE label_en IN ('Dashboard', 'In Store')"))
    op.drop_constraint("fk_admin_nav_items_parent_id", "admin_nav_items", type_="foreignkey")
    op.drop_index("ix_admin_nav_items_parent_id", table_name="admin_nav_items")
    op.drop_column("admin_nav_items", "parent_id")
