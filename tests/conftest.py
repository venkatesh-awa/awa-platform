from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
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
from services import role_service  # noqa: E402


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


def _make_role_user(role_name: str, *, email: str | None = None) -> User:
    role = Role(id=uuid.uuid4(), name=role_name)
    user = User(
        id=uuid.uuid4(),
        email=email or f"{role_name.lower()}@example.test",
        password_hash="hashed",
        first_name="Test",
        last_name=role_name,
        primary_role_id=role.id,
        is_active=True,
        is_email_verified=True,
    )
    user.primary_role = role
    user.created_at = datetime.now(UTC)  # normally a DB server_default; set here for in-memory use
    return user


@pytest.fixture
def test_buyer() -> User:
    return _make_role_user("Buyer", email="buyer@example.test")


@pytest.fixture
def test_staff_user() -> User:
    """An Admin - satisfies both core.roles.STAFF_ROLES and every
    section-specific requirement in core.roles.SECTION_ROLE_REQUIREMENTS."""
    return _make_role_user("Admin", email="admin@example.test")


@pytest.fixture(autouse=True)
def _stub_role_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """api.deps.require_local_role and api/v1/admin.py's section checks call
    role_service.get_user_roles(db, user) to read a user's full role set.
    Stubbing it to the override-injected user's own primary_role - rather
    than driving it through mock_db_session.execute - keeps every route test
    free of a second, role-check-shaped DB call it doesn't care about; tests
    that care about role gating pick the user's role via which fixture/factory
    they use (test_buyer, test_staff_user, make_role_client)."""

    async def _fake_get_user_roles(_db: object, user: User) -> list[Role]:
        return [user.primary_role]

    monkeypatch.setattr(role_service, "get_user_roles", _fake_get_user_roles)


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
def app_with_staff_overrides(mock_db_session: MagicMock, test_staff_user: User):
    app = create_app()

    async def _override_db() -> AsyncGenerator[MagicMock, None]:
        yield mock_db_session

    async def _override_user() -> User:
        return test_staff_user

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_current_local_user] = _override_user
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def staff_client(app_with_staff_overrides) -> AsyncGenerator[AsyncClient, None]:
    """Like `client`, but the authenticated user is an Admin rather than a
    Buyer - for endpoints that are staff-only (api/v1/admin.py,
    api/v1/vehicle_intake.py's write/search endpoints)."""
    transport = ASGITransport(app=app_with_staff_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def make_role_client(mock_db_session: MagicMock):
    """Factory for a client authenticated as an arbitrary single-role user -
    for tests asserting a specific role (e.g. Manager vs Accountant) is
    accepted or rejected by a specific admin section."""

    def _factory(role_name: str) -> AsyncClient:
        user = _make_role_user(role_name)
        app = create_app()

        async def _override_db() -> AsyncGenerator[MagicMock, None]:
            yield mock_db_session

        async def _override_user() -> User:
            return user

        app.dependency_overrides[get_db_session] = _override_db
        app.dependency_overrides[get_current_local_user] = _override_user
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    return _factory


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
