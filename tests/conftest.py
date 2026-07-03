from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault(
    "DATABASE_URL",
    "mssql+aioodbc://test:test@localhost:1433/test?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
os.environ.setdefault("AUTH_ISSUER", "https://test-issuer.example.com/")
os.environ.setdefault("AUTH_AUDIENCE", "api://test")
os.environ.setdefault("AUTH_JWKS_URL", "https://test-issuer.example.com/keys")

from api.deps import get_current_user, get_db_session  # noqa: E402
from core.security import CurrentUser  # noqa: E402
from main import create_app  # noqa: E402


@pytest.fixture
def mock_db_session() -> MagicMock:
    session = MagicMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def test_buyer() -> CurrentUser:
    return CurrentUser(subject="buyer-123", roles=["Buyer"], raw_claims={"sub": "buyer-123"})


@pytest.fixture
def app_with_overrides(mock_db_session: MagicMock, test_buyer: CurrentUser):
    app = create_app()

    async def _override_db() -> AsyncGenerator[MagicMock, None]:
        yield mock_db_session

    async def _override_user() -> CurrentUser:
        return test_buyer

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
