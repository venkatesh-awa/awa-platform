"""Unit tests for the local authentication subsystem.

The service layer is tested against a mocked AsyncSession (same style as
tests/test_content.py) so no real database is required. Password hashing and
token helpers are pure and tested directly.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from jose import jwt

from core.access_tokens import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_token,
)
from core.passwords import hash_password, verify_password
from models.role import Role
from models.user import PasswordResetToken, User
from schemas.auth import SignUpRequest
from services import auth_service
from services.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)

# --- helpers ---------------------------------------------------------------


def _scalar_one_or_none(value: object) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _make_session() -> MagicMock:
    session = MagicMock()
    session.execute = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _make_user(password: str = "Secret123", **overrides: object) -> User:
    buyer_role = Role(id=uuid.uuid4(), name="Buyer")
    user = User(
        email=overrides.get("email", "jane@example.com"),
        password_hash=hash_password(password),
        first_name="Jane",
        last_name="Doe",
        phone=None,
        primary_role_id=buyer_role.id,
        is_active=overrides.get("is_active", True),
        is_email_verified=False,
    )
    user.primary_role = buyer_role
    user.id = uuid.uuid4()
    user.failed_login_attempts = overrides.get("failed_login_attempts", 0)
    user.locked_until = overrides.get("locked_until")
    return user


# --- password hashing ------------------------------------------------------


def test_password_hash_round_trip() -> None:
    h = hash_password("Sup3rSecret")
    assert h != "Sup3rSecret"  # never stored in plaintext
    assert verify_password("Sup3rSecret", h) is True
    assert verify_password("wrong", h) is False


def test_verify_password_tolerates_garbage_hash() -> None:
    assert verify_password("anything", "not-a-valid-hash") is False


# --- access / opaque tokens ------------------------------------------------


def test_access_token_round_trip() -> None:
    uid = uuid.uuid4()
    token, expires_in = create_access_token(uid, ["Buyer"])
    assert expires_in > 0
    claims = decode_access_token(token)
    assert claims is not None
    assert claims.subject == str(uid)
    assert claims.roles == ["Buyer"]


def test_decode_rejects_tampered_token() -> None:
    token, _ = create_access_token(uuid.uuid4(), ["Buyer"])
    assert decode_access_token(token + "x") is None


def test_decode_rejects_expired_token() -> None:
    from core.config import get_settings

    settings = get_settings()
    now = int(time.time())
    expired = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "roles": ["Buyer"],
            "type": "access",
            "iss": settings.auth_local_issuer,
            "iat": now - 100,
            "exp": now - 10,
        },
        settings.auth_jwt_secret,
        algorithm="HS256",
    )
    assert decode_access_token(expired) is None


def test_opaque_token_hash_is_deterministic_and_hides_raw() -> None:
    raw = generate_opaque_token()
    assert hash_token(raw) == hash_token(raw)
    assert raw not in hash_token(raw)
    assert len(hash_token(raw)) == 64


# --- sign up ---------------------------------------------------------------


async def test_sign_up_creates_user_and_verification_token() -> None:
    session = _make_session()
    buyer_role = Role(id=uuid.uuid4(), name="Buyer")
    session.execute.side_effect = [
        _scalar_one_or_none(None),  # email not taken
        _scalar_one_or_none(buyer_role),  # sign_up's own get_role_by_name("Buyer")
        _scalar_one_or_none(buyer_role),  # role_service.assign_role's get_role_by_name("Buyer")
        _scalar_one_or_none(None),  # no existing user_roles row yet
    ]

    added: list[object] = []
    session.add.side_effect = added.append

    async def _flush() -> None:
        for obj in added:
            if isinstance(obj, User) and obj.id is None:
                obj.id = uuid.uuid4()

    session.flush.side_effect = _flush

    data = SignUpRequest(
        email="New.User@Example.com",
        password="Secret123",
        first_name="New",
        last_name="User",
    )
    result = await auth_service.sign_up(session, data)

    assert result.user.email == "new.user@example.com"  # normalized
    assert result.user.password_hash != "Secret123"
    assert result.verification_token
    session.commit.assert_awaited()


async def test_sign_up_rejects_duplicate_email() -> None:
    session = _make_session()
    session.execute.return_value = _scalar_one_or_none(_make_user())

    data = SignUpRequest(
        email="jane@example.com", password="Secret123", first_name="Jane", last_name="Doe"
    )
    with pytest.raises(EmailAlreadyRegisteredError):
        await auth_service.sign_up(session, data)


# --- sign in ---------------------------------------------------------------


async def test_sign_in_success_returns_tokens() -> None:
    session = _make_session()
    user = _make_user(password="Secret123")
    session.execute.return_value = _scalar_one_or_none(user)

    returned_user, tokens = await auth_service.sign_in(session, "jane@example.com", "Secret123")

    assert returned_user is user
    assert tokens.access_token
    assert tokens.refresh_token
    assert decode_access_token(tokens.access_token).subject == str(user.id)
    assert user.failed_login_attempts == 0
    assert user.last_login_at is not None


async def test_sign_in_wrong_password_increments_attempts() -> None:
    session = _make_session()
    user = _make_user(password="Secret123")
    session.execute.return_value = _scalar_one_or_none(user)

    with pytest.raises(InvalidCredentialsError):
        await auth_service.sign_in(session, "jane@example.com", "WrongPass1")

    assert user.failed_login_attempts == 1


async def test_sign_in_locks_after_max_failures() -> None:
    from core.config import get_settings

    max_attempts = get_settings().auth_max_failed_logins
    session = _make_session()
    user = _make_user(password="Secret123", failed_login_attempts=max_attempts - 1)
    session.execute.return_value = _scalar_one_or_none(user)

    with pytest.raises(InvalidCredentialsError):
        await auth_service.sign_in(session, "jane@example.com", "WrongPass1")

    assert user.locked_until is not None


async def test_sign_in_unknown_email_is_invalid_credentials() -> None:
    session = _make_session()
    session.execute.return_value = _scalar_one_or_none(None)

    with pytest.raises(InvalidCredentialsError):
        await auth_service.sign_in(session, "ghost@example.com", "Secret123")


# --- password reset --------------------------------------------------------


async def test_request_password_reset_unknown_email_returns_none() -> None:
    session = _make_session()
    session.execute.return_value = _scalar_one_or_none(None)

    assert await auth_service.request_password_reset(session, "ghost@example.com") is None


async def test_request_password_reset_known_email_returns_token() -> None:
    session = _make_session()
    session.execute.return_value = _scalar_one_or_none(_make_user())

    raw = await auth_service.request_password_reset(session, "jane@example.com")

    assert raw
    session.add.assert_called_once()
    session.commit.assert_awaited()


async def test_reset_password_with_invalid_token_raises() -> None:
    session = _make_session()
    session.execute.return_value = _scalar_one_or_none(None)

    with pytest.raises(InvalidTokenError):
        await auth_service.reset_password(session, "bogus", "NewSecret123")


async def test_reset_password_success_changes_hash_and_consumes_token() -> None:
    session = _make_session()
    user = _make_user(password="OldSecret1")
    old_hash = user.password_hash
    token_row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token("rawtoken"),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        used_at=None,
    )
    # first execute -> select token; second execute -> revoke refresh tokens
    session.execute.side_effect = [_scalar_one_or_none(token_row), MagicMock()]
    session.get.return_value = user

    await auth_service.reset_password(session, "rawtoken", "NewSecret123")

    assert user.password_hash != old_hash
    assert verify_password("NewSecret123", user.password_hash)
    assert token_row.used_at is not None


# --- HTTP layer (error mapping / validation) -------------------------------


async def test_signin_endpoint_maps_invalid_credentials_to_401(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _scalar_one_or_none(None)

    response = await client.post(
        "/api/v1/auth/signin", json={"email": "ghost@example.com", "password": "Secret123"}
    )

    assert response.status_code == 401


async def test_signup_endpoint_rejects_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "a@b.com", "password": "short", "first_name": "A", "last_name": "B"},
    )
    assert response.status_code == 422


async def test_forgot_password_is_generic_for_unknown_email(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _scalar_one_or_none(None)

    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "ghost@example.com"}
    )

    assert response.status_code == 200
    assert "message" in response.json()


async def test_me_requires_bearer_token(unauthenticated_client: AsyncClient) -> None:
    response = await unauthenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 401
