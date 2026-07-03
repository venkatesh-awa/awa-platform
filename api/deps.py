"""Shared FastAPI dependencies re-exported for convenient importing in routers."""

from __future__ import annotations

from core.database import get_db_session
from core.redis import get_redis
from core.security import CurrentUser, get_current_user, require_role

__all__ = ["get_db_session", "get_redis", "CurrentUser", "get_current_user", "require_role"]
