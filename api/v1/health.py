"""Liveness and readiness endpoints. Kubernetes uses these for pod health
(see infra/k8s deployment manifests) - liveness must never depend on
downstream systems, readiness must.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from core.database import check_db_health
from core.redis import check_redis_health

router = APIRouter(tags=["health"])


@router.get("/livez", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    """Process is up and able to serve requests. Never checks downstream dependencies -
    a flaky database should not cause Kubernetes to restart a healthy pod."""
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness probe")
async def readiness(response: Response) -> dict[str, object]:
    """Process is ready to receive traffic - all critical dependencies reachable."""
    db_ok = await check_db_health()
    redis_ok = await check_redis_health()
    ready = db_ok and redis_ok

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if ready else "degraded",
        "checks": {"database": db_ok, "redis": redis_ok},
    }
