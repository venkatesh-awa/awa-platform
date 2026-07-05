from __future__ import annotations

from fastapi import APIRouter

from api.v1 import admin, auctions, auth, content, health, vehicle_intake

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(auctions.router)
api_router.include_router(content.router)
api_router.include_router(admin.router)
api_router.include_router(vehicle_intake.router)
