"""menu item metadata for authenticated header controls

Revision ID: 0004_menu_item_metadata
Revises: 0003_auth_tables
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_menu_item_metadata"
down_revision: str | None = "0003_auth_tables"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def upgrade() -> None:
    op.add_column("menu_items", sa.Column("icon_class", sa.String(length=100), nullable=True))
    op.add_column(
        "menu_items",
        sa.Column("item_type", sa.String(length=30), nullable=False, server_default="link"),
    )
    op.add_column(
        "menu_items",
        sa.Column("visibility", sa.String(length=30), nullable=False, server_default="all"),
    )

    op.execute(
        sa.text(
            """
            UPDATE menu_items
            SET visibility = 'anonymous'
            WHERE LOWER(label_en) IN ('sign up', 'log in', 'login', 'sign in', 'register')
               OR LOWER(url) IN ('/login', '/sign-up', '/signup', '/register', '/myportal/oidc/etdx1')
            """
        )
    )

    menu_items = sa.table(
        "menu_items",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("parent_id", sa.Uuid(as_uuid=True)),
        sa.column("label_en", sa.Unicode(length=100)),
        sa.column("label_ar", sa.Unicode(length=100)),
        sa.column("url", sa.String(length=500)),
        sa.column("icon_class", sa.String(length=100)),
        sa.column("item_type", sa.String(length=30)),
        sa.column("visibility", sa.String(length=30)),
        sa.column("opens_new_tab", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )

    admin_id = _uuid()
    op.bulk_insert(
        menu_items,
        [
            {
                "id": admin_id,
                "parent_id": None,
                "label_en": "Admin Menu",
                "label_ar": "قائمة الإدارة",
                "url": "#",
                "icon_class": "fa-solid fa-user-shield",
                "item_type": "dropdown",
                "visibility": "authenticated",
                "opens_new_tab": False,
                "sort_order": 90,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "parent_id": admin_id,
                "label_en": "Dashboard",
                "label_ar": "لوحة التحكم",
                "url": "/admin",
                "icon_class": "fa-solid fa-gauge-high",
                "item_type": "link",
                "visibility": "authenticated",
                "opens_new_tab": False,
                "sort_order": 1,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "parent_id": admin_id,
                "label_en": "Auctions",
                "label_ar": "المزادات",
                "url": "/admin/auctions",
                "icon_class": "fa-solid fa-gavel",
                "item_type": "link",
                "visibility": "authenticated",
                "opens_new_tab": False,
                "sort_order": 2,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "parent_id": admin_id,
                "label_en": "Users",
                "label_ar": "المستخدمون",
                "url": "/admin/users",
                "icon_class": "fa-solid fa-users",
                "item_type": "link",
                "visibility": "authenticated",
                "opens_new_tab": False,
                "sort_order": 3,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "parent_id": None,
                "label_en": "Notifications",
                "label_ar": "الإشعارات",
                "url": "#notifications",
                "icon_class": "fa-solid fa-bell",
                "item_type": "notification",
                "visibility": "authenticated",
                "opens_new_tab": False,
                "sort_order": 91,
                "is_active": True,
            },
            {
                "id": _uuid(),
                "parent_id": None,
                "label_en": "Profile",
                "label_ar": "الملف الشخصي",
                "url": "/profile",
                "icon_class": "fa-solid fa-circle-user",
                "item_type": "profile",
                "visibility": "authenticated",
                "opens_new_tab": False,
                "sort_order": 92,
                "is_active": True,
            },
        ],
    )

    op.alter_column("menu_items", "item_type", server_default=None)
    op.alter_column("menu_items", "visibility", server_default=None)


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM menu_items
            WHERE item_type IN ('notification', 'profile')
               OR label_en IN ('Admin Menu', 'Dashboard', 'Auctions', 'Users')
            """
        )
    )
    op.drop_column("menu_items", "visibility")
    op.drop_column("menu_items", "item_type")
    op.drop_column("menu_items", "icon_class")
