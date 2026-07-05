from __future__ import annotations

import os
import uuid
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

from api.deps import get_current_local_user, get_db_session  # noqa: E402
from main import create_app  # noqa: E402
from models.role import Role  # noqa: E402
from models.user import User  # noqa: E402


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
def test_buyer() -> User:
    buyer_role = Role(id=uuid.uuid4(), name="Buyer")
    user = User(
        id=uuid.uuid4(),
        email="buyer@example.test",
        password_hash="hashed",
        first_name="Test",
        last_name="Buyer",
        primary_role_id=buyer_role.id,
        is_active=True,
        is_email_verified=True,
    )
    user.primary_role = buyer_role
    return user


@pytest.fixture
def app_with_overrides(mock_db_session: MagicMock, test_buyer: User):
    app = create_app()

    async def _override_db() -> AsyncGenerator[MagicMock, None]:
        yield mock_db_session

    async def _override_user() -> User:
        return test_buyer

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_current_local_user] = _override_user
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def unauthenticated_client(mock_db_session: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    """Like `client`, but doesn't override get_current_local_user - for tests
    that exercise real bearer-token enforcement (e.g. missing/invalid token)."""
    app = create_app()

    async def _override_db() -> AsyncGenerator[MagicMock, None]:
        yield mock_db_session

    app.dependency_overrides[get_db_session] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
