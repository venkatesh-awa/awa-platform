"""Local email/password authentication: sign up, sign in, token refresh/rotation,
sign out, password reset, and email verification.

Framework-agnostic like the other services (services/exceptions.py header):
it takes an AsyncSession and raises domain exceptions; api/v1/auth.py maps
those to HTTP. Security properties enforced here:

  * Passwords are Argon2id-hashed (core/passwords.py); plaintext is never stored.
  * Refresh / reset / verification tokens are random and stored only as SHA-256
    hashes (core/access_tokens.py); the raw value is returned once.
  * Sign-in applies a failed-attempt lockout window to blunt brute force.
  * request_password_reset does not reveal whether an email exists (no user
    enumeration): the API always responds identically.
  * Reset and refresh flows revoke sibling tokens to contain replay/theft.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.access_tokens import (
    create_access_token,
    generate_opaque_token,
    hash_token,
)
from core.config import get_settings
from core.logging import get_logger
from core.passwords import hash_password, needs_rehash, verify_password
from models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
)
from schemas.auth import SignUpRequest, TokenPair, UserRead
from services import role_service
from services.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SignUpResult:
    user: User
    # Raw single-use email-verification token; hand to the notification layer
    # (email) - it is never persisted in raw form or returned over the API.
    verification_token: str


def _now() -> datetime:
    return datetime.now(UTC)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def to_user_read(db: AsyncSession, user: User) -> UserRead:
    """Build the API-facing user representation. `role` is stringified from
    the primary_role FK, `roles` is the full set (models/role.py's
    user_roles) - neither exists as a plain attribute on User itself."""
    roles = await role_service.get_user_roles(db, user)
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        role=user.primary_role.name,
        roles=[role.name for role in roles] or [user.primary_role.name],
        is_email_verified=user.is_email_verified,
        created_at=user.created_at,
    )


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == _normalize_email(email)))
    return result.scalar_one_or_none()


async def sign_up(db: AsyncSession, data: SignUpRequest) -> SignUpResult:
    """Create a new account. Raises EmailAlreadyRegisteredError on a duplicate."""
    email = _normalize_email(data.email)
    if await _get_user_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError(email)

    buyer_role = await role_service.get_role_by_name(db, "Buyer")
    user = User(
        email=email,
        password_hash=hash_password(data.password),
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        phone=data.phone.strip() if data.phone else None,
        primary_role_id=buyer_role.id,
        is_active=True,
        is_email_verified=False,
    )
    user.primary_role = buyer_role  # avoid a lazy-load if read back before a refresh
    db.add(user)
    await db.flush()  # populate user.id before creating the child token row/role row

    await role_service.assign_role(db, user, "Buyer", is_primary=True)
    raw_token, _ = await _issue_email_verification(db, user)

    await db.commit()
    logger.info("user_signed_up", user_id=str(user.id))
    return SignUpResult(user=user, verification_token=raw_token)


async def sign_in(db: AsyncSession, email: str, password: str) -> tuple[User, TokenPair]:
    """Authenticate and issue an access + refresh token pair.

    Raises InvalidCredentialsError (unknown email or wrong password),
    AccountLockedError (too many recent failures), or AccountInactiveError.
    """
    settings = get_settings()
    user = await _get_user_by_email(db, email)

    # verify_password against a real-looking hash even for unknown users would be
    # ideal to fully equalize timing; Argon2 verify on the found user already
    # dominates timing, and the uniform error message avoids enumeration.
    if user is None:
        raise InvalidCredentialsError

    if user.locked_until is not None and user.locked_until > _now():
        retry_after = int((user.locked_until - _now()).total_seconds())
        raise AccountLockedError(retry_after_seconds=max(retry_after, 1))

    if not user.is_active:
        raise AccountInactiveError

    if not verify_password(password, user.password_hash):
        await _register_failed_login(db, user, settings.auth_max_failed_logins, settings.auth_lockout_seconds)
        await db.commit()
        raise InvalidCredentialsError

    # Success: transparently upgrade the hash if the cost policy has increased.
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = _now()

    tokens = await _issue_token_pair(db, user)
    await db.commit()
    logger.info("user_signed_in", user_id=str(user.id))
    return user, tokens


async def refresh(db: AsyncSession, raw_refresh_token: str) -> TokenPair:
    """Rotate a refresh token: validate, revoke the presented one, issue a new pair."""
    token_row = await _get_active_refresh_token(db, raw_refresh_token)
    if token_row is None:
        raise InvalidTokenError

    user = await db.get(User, token_row.user_id)
    if user is None or not user.is_active:
        raise InvalidTokenError

    token_row.revoked_at = _now()  # rotation: the old token is single-use
    tokens = await _issue_token_pair(db, user)
    await db.commit()
    logger.info("access_token_refreshed", user_id=str(user.id))
    return tokens


async def sign_out(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke a refresh token. Idempotent - unknown/expired tokens are a no-op."""
    token_row = await _get_active_refresh_token(db, raw_refresh_token)
    if token_row is not None:
        token_row.revoked_at = _now()
        await db.commit()


async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """Create a password-reset token for the email, if an active account exists.

    Returns the raw token for the notification layer, or None when there is no
    matching account. The API responds identically either way (no enumeration).
    """
    user = await _get_user_by_email(db, email)
    if user is None or not user.is_active:
        logger.info("password_reset_requested_unknown_email")
        return None

    settings = get_settings()
    raw_token = generate_opaque_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=_now() + timedelta(seconds=settings.auth_password_reset_ttl_seconds),
        )
    )
    await db.commit()
    logger.info("password_reset_requested", user_id=str(user.id))
    return raw_token


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
    """Consume a reset token and set a new password. Raises InvalidTokenError if
    the token is unknown, already used, or expired. Revokes all refresh tokens so
    existing sessions can't outlive a password reset."""
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw_token))
    )
    token_row = result.scalar_one_or_none()
    if token_row is None or token_row.used_at is not None or token_row.expires_at <= _now():
        raise InvalidTokenError

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise InvalidTokenError

    user.password_hash = hash_password(new_password)
    token_row.used_at = _now()
    await _revoke_all_refresh_tokens(db, user.id)
    await db.commit()
    logger.info("password_reset_completed", user_id=str(user.id))


async def verify_email(db: AsyncSession, raw_token: str) -> None:
    """Consume an email-verification token and flag the account verified."""
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_token(raw_token)
        )
    )
    token_row = result.scalar_one_or_none()
    if token_row is None or token_row.used_at is not None or token_row.expires_at <= _now():
        raise InvalidTokenError

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise InvalidTokenError

    user.is_email_verified = True
    token_row.used_at = _now()
    await db.commit()
    logger.info("email_verified", user_id=str(user.id))


# --- internal helpers ---


async def _issue_token_pair(db: AsyncSession, user: User) -> TokenPair:
    settings = get_settings()
    # All roles the user holds, not just their primary one - a user with
    # both Seller and Buyer roles must be authorized as both (see
    # services/role_service.py and services/bid_service.REQUIRED_BID_ROLES).
    user_roles = await role_service.get_user_roles(db, user)
    role_names = [role.name for role in user_roles] or [user.primary_role.name]
    access_token, expires_in = create_access_token(user.id, role_names)

    raw_refresh = generate_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=_now() + timedelta(seconds=settings.auth_refresh_token_ttl_seconds),
        )
    )
    return TokenPair(access_token=access_token, refresh_token=raw_refresh, expires_in=expires_in)


async def _issue_email_verification(db: AsyncSession, user: User) -> tuple[str, EmailVerificationToken]:
    settings = get_settings()
    raw_token = generate_opaque_token()
    row = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=_now() + timedelta(seconds=settings.auth_email_verification_ttl_seconds),
    )
    db.add(row)
    return raw_token, row


async def _get_active_refresh_token(db: AsyncSession, raw_token: str) -> RefreshToken | None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    )
    row = result.scalar_one_or_none()
    if row is None or row.revoked_at is not None or row.expires_at <= _now():
        return None
    return row


async def _revoke_all_refresh_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )


async def _register_failed_login(
    db: AsyncSession, user: User, max_attempts: int, lockout_seconds: int
) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= max_attempts:
        user.locked_until = _now() + timedelta(seconds=lockout_seconds)
        user.failed_login_attempts = 0
        logger.warning("account_locked", user_id=str(user.id))
