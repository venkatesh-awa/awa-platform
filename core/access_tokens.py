"""Tokens issued by THIS service for the local email/password flow.

Two kinds:
  * Access tokens - short-lived HS256 JWTs carrying the user id + roles. Signed
    with ``auth_jwt_secret`` (symmetric), distinct from the RS256 external-IdP
    tokens verified in core/security.py. Verified locally, no network call.
  * Opaque tokens - random high-entropy strings used as refresh, password-reset,
    and email-verification tokens. Only their SHA-256 hash is ever stored, so a
    database leak does not expose usable tokens; the raw value is shown to the
    client exactly once.
"""

from __future__ import annotations

import hashlib
import secrets
import time
import uuid
from dataclasses import dataclass

from jose import jwt
from jose.exceptions import JOSEError

from core.config import get_settings

_ALGORITHM = "HS256"
_TOKEN_TYPE = "access"  # noqa: S105 - a claim label, not a secret


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    subject: str
    roles: list[str]


def create_access_token(user_id: uuid.UUID, roles: list[str]) -> tuple[str, int]:
    """Return ``(jwt, expires_in_seconds)`` for the given user."""
    settings = get_settings()
    now = int(time.time())
    expires_in = settings.auth_access_token_ttl_seconds
    claims = {
        "sub": str(user_id),
        "roles": roles,
        "type": _TOKEN_TYPE,
        "iss": settings.auth_local_issuer,
        "iat": now,
        "exp": now + expires_in,
        "jti": secrets.token_urlsafe(16),
    }
    token = jwt.encode(claims, settings.auth_jwt_secret, algorithm=_ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> AccessTokenClaims | None:
    """Verify signature/issuer/expiry of a locally-issued access token.

    Returns None for anything invalid (bad signature, expired, wrong issuer or
    token type) so the caller can raise a uniform 401 without leaking specifics.
    """
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=[_ALGORITHM],
            issuer=settings.auth_local_issuer,
            options={"verify_exp": True, "verify_iss": True, "require_sub": True},
        )
    except JOSEError:
        return None

    if claims.get("type") != _TOKEN_TYPE:
        return None
    subject = str(claims.get("sub", ""))
    if not subject:
        return None
    roles = claims.get("roles", [])
    if not isinstance(roles, list):
        roles = []
    return AccessTokenClaims(subject=subject, roles=[str(r) for r in roles])


def generate_opaque_token() -> str:
    """A URL-safe, high-entropy token to hand to the client (refresh / reset / verify)."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Deterministic SHA-256 hex digest stored in place of the raw token.

    A plain (unsalted) hash is appropriate here - unlike passwords these values
    are already 256 bits of entropy, so they are not brute-forceable, and a
    deterministic digest is what lets us look the token up by equality.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
