"""Shared FastAPI dependencies re-exported for convenient importing in routers."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.access_tokens import decode_access_token
from core.database import get_db_session
from core.redis import get_redis
from core.security import CurrentUser, get_current_user, require_role
from models.user import User
from services import auth_service, role_service

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_local_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Resolve the local User row from a token issued by THIS service's
    email/password flow (core/access_tokens.py) - distinct from
    get_current_user, which verifies external-IdP tokens (core/security.py).

    Anything that writes a row carrying a foreign key into the local `users`
    table (e.g. Bid.bidder_id) must authenticate through here: an external
    IdP token's `sub` has no guaranteed relationship to a local user row,
    since the two token issuers are entirely separate trust boundaries.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials:
        raise unauthorized

    claims = decode_access_token(credentials.credentials)
    if claims is None:
        raise unauthorized

    try:
        user_id = uuid.UUID(claims.subject)
    except ValueError as exc:
        raise unauthorized from exc

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_local_role(*role_names: str) -> Callable[..., Coroutine[object, object, User]]:
    """Dependency factory gating a local-auth endpoint by role, checking a
    user's full set of assigned roles (models/role.py's `user_roles`) rather
    than only their primary one - e.g. an Admin who also holds Buyer should
    still pass `require_local_role("Admin")`.
    """

    async def _checker(
        user: User = Depends(get_current_local_user),
        db: AsyncSession = Depends(get_db_session),
    ) -> User:
        held = {role.name for role in await role_service.get_user_roles(db, user)}
        if held.isdisjoint(role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {' or '.join(role_names)}",
            )
        return user

    return _checker


__all__ = [
    "get_db_session",
    "get_redis",
    "CurrentUser",
    "get_current_user",
    "get_current_local_user",
    "require_role",
    "require_local_role",
]
