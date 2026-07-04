"""Admin dashboard chrome endpoints - sidebar nav and per-section card grids.

Unauthenticated by design, like api/v1/content.py: this only serves
navigation labels/icons, never seller or user data. The frontend still gates
the "Admin" entry point behind the authenticated header menu (see
models/content.py's Admin Menu seed) - actual seller/user data endpoints
will need their own auth once they exist.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db_session
from schemas.admin import AdminDashboardCardRead, AdminNavItemRead, VehicleStatusMetricRead
from schemas.vehicle_payment import VehiclePaymentRecordPage, VehiclePaymentStatusCounts
from services import admin_service, vehicle_payment_service

router = APIRouter(prefix="/admin", tags=["admin"])

LangQuery = Literal["en", "ar"]


@router.get("/nav", response_model=list[AdminNavItemRead])
async def get_admin_nav(
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> list[AdminNavItemRead]:
    return await admin_service.get_admin_nav(db, lang)


@router.get("/dashboard-cards", response_model=list[AdminDashboardCardRead])
async def get_admin_dashboard_cards(
    section: str = Query(...),
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> list[AdminDashboardCardRead]:
    return await admin_service.get_admin_dashboard_cards(db, lang, section)


@router.get("/vehicle-status-metrics", response_model=list[VehicleStatusMetricRead])
async def get_vehicle_status_metrics(
    group: str = Query(...),
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> list[VehicleStatusMetricRead]:
    return await admin_service.get_vehicle_status_metrics(db, lang, group)


@router.get("/vehicle-payment-status-count", response_model=VehiclePaymentStatusCounts)
async def get_vehicle_payment_status_count(
    db: AsyncSession = Depends(get_db_session),
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
