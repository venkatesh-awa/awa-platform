"""Read operations for the admin dashboard chrome (sidebar nav + per-section
card grids). Public/unauthenticated by design, matching services/content_service.py -
this only exposes navigation labels and icons, no seller/user data.
"""

from __future__ import annotations

from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin import AdminDashboardCard, AdminNavItem, VehicleStatusMetric
from schemas.admin import AdminDashboardCardRead, AdminNavItemRead, VehicleStatusMetricRead

Lang = Literal["en", "ar"]


def _pick(en: str | None, ar: str | None, lang: Lang) -> str:
    if lang == "ar" and ar:
        return ar
    return en or ""


async def get_admin_nav(db: AsyncSession, lang: Lang) -> list[AdminNavItemRead]:
    result = await db.execute(
        select(AdminNavItem).where(AdminNavItem.is_active).order_by(AdminNavItem.sort_order)
    )
    return [
        AdminNavItemRead(
            id=row.id,
            parent_id=row.parent_id,
            label=_pick(row.label_en, row.label_ar, lang),
            icon_class=row.icon_class,
            url=row.url,
            sort_order=row.sort_order,
        )
        for row in result.scalars().all()
    ]


async def get_vehicle_status_metrics(
    db: AsyncSession, lang: Lang, group_key: str
) -> list[VehicleStatusMetricRead]:
    result = await db.execute(
        select(VehicleStatusMetric)
        .where(VehicleStatusMetric.is_active, VehicleStatusMetric.group_key == group_key)
        .order_by(VehicleStatusMetric.sort_order)
    )
    return [
        VehicleStatusMetricRead(
            id=row.id,
            group_key=row.group_key,
            stat_key=row.stat_key,
            label=_pick(row.label_en, row.label_ar, lang),
            icon_class=row.icon_class,
            image_url=row.image_url,
            color_class=row.color_class,
            sort_order=row.sort_order,
        )
        for row in result.scalars().all()
    ]


async def get_admin_dashboard_cards(
    db: AsyncSession, lang: Lang, section_key: str
) -> list[AdminDashboardCardRead]:
    result = await db.execute(
        select(AdminDashboardCard)
        .where(AdminDashboardCard.is_active, AdminDashboardCard.section_key == section_key)
        .order_by(AdminDashboardCard.sort_order)
    )
    return [
        AdminDashboardCardRead(
            id=row.id,
            section_key=row.section_key,
            label=_pick(row.label_en, row.label_ar, lang),
            description=_pick(row.description_en, row.description_ar, lang) or None,
            icon_class=row.icon_class,
            url=row.url,
            image_url=row.image_url,
            sort_order=row.sort_order,
        )
        for row in result.scalars().all()
    ]
