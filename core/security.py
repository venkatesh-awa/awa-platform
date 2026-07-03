"""Authentication: verifies bearer JWTs issued by the configured identity
provider (Azure B2C and/or UAE Pass, per BRD R036/R237/R018). This module
only verifies tokens - it does not issue them; token issuance is delegated
entirely to the identity provider, which is the correct security boundary.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JOSEError

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
_bearer_scheme = HTTPBearer(auto_error=False)

_jwks_cache: dict[str, object] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 3600


@dataclass(frozen=True, slots=True)
class CurrentUser:
    subject: str
    roles: list[str]
    raw_claims: dict[str, object]

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def _get_jwks() -> dict:
    now = time.time()
    if _jwks_cache["keys"] is not None and (now - _jwks_cache["fetched_at"]) < _JWKS_TTL_SECONDS:
        return _jwks_cache["keys"]  # type: ignore[return-value]

    settings = get_settings()
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(settings.auth_jwks_url)
        response.raise_for_status()
        keys = response.json()

    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


async def _decode_token(token: str) -> dict[str, object]:
    settings = get_settings()
    try:
        jwks = await _get_jwks()
        claims = jwt.decode(
            token,
            jwks,
            algorithms=settings.auth_jwt_algorithms,
            audience=settings.auth_audience,
            issuer=settings.auth_issuer,
            options={"verify_exp": True, "verify_aud": True, "verify_iss": True},
        )
        return claims
    except JOSEError as exc:
        logger.warning("jwt_verification_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("jwks_fetch_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = await _decode_token(credentials.credentials)
    subject = str(claims.get("sub", ""))
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    roles = claims.get("roles", [])
    if not isinstance(roles, list):
        roles = []

    return CurrentUser(subject=subject, roles=[str(r) for r in roles], raw_claims=claims)


def require_role(role: str):
    """Dependency factory for endpoint-level RBAC, e.g. Depends(require_role("Buyer"))."""

    async def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {role}",
            )
        return user

    return _checker
