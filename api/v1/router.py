from __future__ import annotations

from fastapi import APIRouter

from api.v1 import auctions, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auctions.router)
