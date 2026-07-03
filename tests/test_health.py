from __future__ import annotations

from httpx import AsyncClient


async def test_liveness_always_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/livez")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_degraded_without_infra(client: AsyncClient) -> None:
    """Without a real database/redis connection, readiness must report degraded
    (503) rather than crash - this is exactly the behavior Kubernetes relies on
    to keep a pod out of the load-balancer rotation until it's actually ready."""
    response = await client.get("/api/v1/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] is False
    assert body["checks"]["redis"] is False
