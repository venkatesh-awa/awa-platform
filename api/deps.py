"""Shared FastAPI dependencies re-exported for convenient importing in routers."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.access_tokens import decode_access_token
from core.database import get_db_session
from core.redis import get_redis
from core.security import CurrentUser, get_current_user, require_role
from models.user import User
from services import auth_service

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


__all__ = [
    "get_db_session",
    "get_redis",
    "CurrentUser",
    "get_current_user",
    "get_current_local_user",
    "require_role",
]
