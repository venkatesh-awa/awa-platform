"""ensure Admin sidebar group (Overview, Dashboard, In Store) with FA icons

The '/admin' row doubles as the sidebar's "Admin" section title and its
first link (rendered as "Overview" by the frontend). This migration makes
sure that row plus its two children exist, are parented correctly, and each
carry a Font Awesome icon:

  Admin/Overview  /admin            fa-solid fa-border-all
  Dashboard       /admin/dashboard  fa-solid fa-gauge-high
  In Store        /admin/instore    fa-solid fa-store

Idempotent: rows are matched by URL and updated in place, inserted only if
missing (e.g. a fresh environment that skipped 0011's seed data).

Revision ID: 0032_admin_nav_overview_icons
Revises: 0031_seed_role_demo_users
Create Date: 2026-07-05

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0032_admin_nav_overview_icons"
down_revision: str | None = "0031_seed_role_demo_users"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_ADMIN_URL = "/admin"
_ADMIN_ICON = "fa-solid fa-border-all"

# (label_en, label_ar, icon_class, url, sort_order)
_CHILD_ITEMS: list[tuple[str, str, str, str, int]] = [
    ("Dashboard", "لوحة التحكم", "fa-solid fa-gauge-high", "/admin/dashboard", 1),
    ("In Store", "داخل المتجر", "fa-solid fa-store", "/admin/instore", 2),
]

_INSERT_SQL = sa.text(
    """
    INSERT INTO admin_nav_items
        (id, parent_id, label_en, label_ar, icon_class, url, sort_order, is_active)
    VALUES
        (:id, :parent_id, :label_en, :label_ar, :icon_class, :url, :sort_order, :is_active)
    """
)


def upgrade() -> None:
    bind = op.get_bind()

    admin_id = bind.execute(
        sa.text("SELECT id FROM admin_nav_items WHERE url = :url"), {"url": _ADMIN_URL}
    ).scalar()

    if admin_id is None:
        admin_id = uuid.uuid4()
        bind.execute(
            _INSERT_SQL,
            {
                "id": admin_id,
                "parent_id": None,
                "label_en": "Admin",
                "label_ar": "الإدارة العامة",
                "icon_class": _ADMIN_ICON,
                "url": _ADMIN_URL,
                "sort_order": 7,
                "is_active": True,
            },
        )
    else:
        # 0026 cleared this icon; the sidebar's Overview link now shows one.
        bind.execute(
            sa.text(
                """
                UPDATE admin_nav_items
                SET icon_class = :icon_class,
                    is_active = :is_active
                WHERE id = :id
                """
            ),
            {"icon_class": _ADMIN_ICON, "is_active": True, "id": admin_id},
        )

    for label_en, label_ar, icon_class, url, sort_order in _CHILD_ITEMS:
        existing_id = bind.execute(
            sa.text("SELECT id FROM admin_nav_items WHERE url = :url"), {"url": url}
        ).scalar()
        params = {
            "parent_id": admin_id,
            "label_en": label_en,
            "label_ar": label_ar,
            "icon_class": icon_class,
            "url": url,
            "sort_order": sort_order,
            "is_active": True,
        }
        if existing_id is None:
            bind.execute(_INSERT_SQL, {"id": uuid.uuid4(), **params})
        else:
            bind.execute(
                sa.text(
                    """
                    UPDATE admin_nav_items
                    SET parent_id = :parent_id,
                        label_en = :label_en,
                        label_ar = :label_ar,
                        icon_class = :icon_class,
                        sort_order = :sort_order,
                        is_active = :is_active
                    WHERE id = :id
                    """
                ),
                {"id": existing_id, **params},
            )


def downgrade() -> None:
    # Restore the pre-0032 icon state (0026 nulled '/admin', 0011 seeded the
    # children without icons). Rows themselves are left in place.
    op.execute(
        sa.text(
            """
            UPDATE admin_nav_items
            SET icon_class = NULL
            WHERE url IN ('/admin', '/admin/dashboard', '/admin/instore')
            """
        )
    )
