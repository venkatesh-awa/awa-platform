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
from schemas.admin import AdminDashboardCardRead, AdminNavItemRead
from services import admin_service

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
