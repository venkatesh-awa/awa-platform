"""Admin dashboard chrome endpoints - sidebar nav and per-section card grids,
plus dashboard-tier vehicle/payment data.

Staff-only (core.roles.STAFF_ROLES): a marketplace Buyer/Seller must never
reach any of this, per api/deps.require_local_role. Management and Accountant
are further restricted to their own role (or Admin) - see
core.roles.SECTION_ROLE_REQUIREMENTS - since they carry section-specific data
a generic staff member (e.g. Operations) shouldn't see.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db_session, require_local_role
from core.roles import SECTION_ROLE_REQUIREMENTS, STAFF_ROLES
from models.user import User
from schemas.admin import (
    AdminDashboardCardRead,
    AdminNavItemRead,
    AdminUserCountsRead,
    VehicleStatusMetricRead,
)
from schemas.vehicle_payment import (
    VehicleInStoreRecordPage,
    VehiclePaymentRecordPage,
    VehiclePaymentStatusCounts,
)
from services import admin_service, role_service, vehicle_payment_service

router = APIRouter(prefix="/admin", tags=["admin"])

LangQuery = Literal["en", "ar"]

_require_staff = require_local_role(*STAFF_ROLES)


def _section_key_from_url(url: str) -> str | None:
    """"/admin/management" -> "management"; "/admin" or "/admin/" -> None."""
    prefix = "/admin/"
    if not url.startswith(prefix):
        return None
    return url[len(prefix) :].split("/")[0] or None


async def _ensure_section_access(user: User, db: AsyncSession, section: str) -> None:
    required = SECTION_ROLE_REQUIREMENTS.get(section)
    if required is None:
        return
    held = {role.name for role in await role_service.get_user_roles(db, user)}
    if held.isdisjoint(required):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires role: {' or '.join(required)}",
        )


@router.get("/nav", response_model=list[AdminNavItemRead])
async def get_admin_nav(
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(_require_staff),
) -> list[AdminNavItemRead]:
    items = await admin_service.get_admin_nav(db, lang)
    held = {role.name for role in await role_service.get_user_roles(db, user)}
    return [
        item
        for item in items
        if (section := _section_key_from_url(item.url)) is None
        or (required := SECTION_ROLE_REQUIREMENTS.get(section)) is None
        or not held.isdisjoint(required)
    ]


@router.get("/dashboard-cards", response_model=list[AdminDashboardCardRead])
async def get_admin_dashboard_cards(
    section: str = Query(...),
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(_require_staff),
) -> list[AdminDashboardCardRead]:
    await _ensure_section_access(user, db, section)
    return await admin_service.get_admin_dashboard_cards(db, lang, section)


@router.get("/user-counts", response_model=AdminUserCountsRead)
async def get_admin_user_counts(
    db: AsyncSession = Depends(get_db_session),
    _user: User = Depends(_require_staff),
) -> AdminUserCountsRead:
    return await admin_service.get_admin_user_counts(db)


@router.get("/vehicle-status-metrics", response_model=list[VehicleStatusMetricRead])
async def get_vehicle_status_metrics(
    group: str = Query(...),
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(_require_staff),
) -> list[VehicleStatusMetricRead]:
    await _ensure_section_access(user, db, group)
    return await admin_service.get_vehicle_status_metrics(db, lang, group)


@router.get("/vehicle-payment-status-count", response_model=VehiclePaymentStatusCounts)
async def get_vehicle_payment_status_count(
    db: AsyncSession = Depends(get_db_session),
    _user: User = Depends(_require_staff),
) -> VehiclePaymentStatusCounts:
    return await vehicle_payment_service.get_vehicle_payment_status_counts(db)


@router.get("/vehicle-payment-status", response_model=VehiclePaymentRecordPage)
async def get_vehicle_payment_status(
    status: str = Query(default="ALL"),
    lot_no: str = Query(default=""),
    chassis_number: str = Query(default=""),
    buyer_name: str = Query(default=""),
    seller_name: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: User = Depends(_require_staff),
) -> VehiclePaymentRecordPage:
    return await vehicle_payment_service.get_vehicle_payment_records(
        db,
        status=status,
        lot_no=lot_no,
        chassis_number=chassis_number,
        buyer_name=buyer_name,
        seller_name=seller_name,
        page=page,
        page_size=page_size,
    )


@router.get("/vehicle-in-store", response_model=VehicleInStoreRecordPage)
async def get_vehicle_in_store(
    id_search: str = Query(default="", alias="id"),
    chassis_number: str = Query(default=""),
    seller_name: str = Query(default=""),
    location: str = Query(default=""),
    sort_by: str = Query(default="id"),
    sort_dir: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: User = Depends(_require_staff),
) -> VehicleInStoreRecordPage:
    return await vehicle_payment_service.get_vehicle_in_store_records(
        db,
        id_search=id_search,
        chassis_number=chassis_number,
        seller_name=seller_name,
        location=location,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
