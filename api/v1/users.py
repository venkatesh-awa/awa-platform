"""User role management: lets an Admin grant/revoke additional roles on top
of a user's primary one (e.g. making an existing Seller also a Buyer, or an
Inspector also a Seller) - see services/role_service.py and models/role.py
for the underlying many-to-many `user_roles` table this operates on.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_local_user, get_db_session, require_local_role
from models.role import Role
from models.user import User
from schemas.role import RoleRead, UserRoleAssignRequest
from services import auth_service, role_service
from services.exceptions import LastRoleRemovalError, RoleNotFoundError

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/roles", response_model=list[RoleRead])
async def get_my_roles(
    user: User = Depends(get_current_local_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Role]:
    return await role_service.get_user_roles(db, user)


async def _get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/{user_id}/roles", response_model=list[RoleRead])
async def get_user_roles(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(require_local_role("Admin")),
) -> list[Role]:
    user = await _get_user_or_404(db, user_id)
    return await role_service.get_user_roles(db, user)


@router.post(
    "/{user_id}/roles",
    response_model=list[RoleRead],
    status_code=status.HTTP_201_CREATED,
    summary="Grant a role to a user (e.g. make a Seller also a Buyer)",
)
async def assign_user_role(
    user_id: uuid.UUID,
    payload: UserRoleAssignRequest,
    db: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(require_local_role("Admin")),
) -> list[Role]:
    user = await _get_user_or_404(db, user_id)
    try:
        await role_service.assign_role(db, user, payload.role_name, is_primary=payload.is_primary)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    await db.commit()
    return await role_service.get_user_roles(db, user)


@router.delete(
    "/{user_id}/roles/{role_name}",
    response_model=list[RoleRead],
    summary="Revoke a role from a user (refused if it's their only remaining role)",
)
async def revoke_user_role(
    user_id: uuid.UUID,
    role_name: str,
    db: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(require_local_role("Admin")),
) -> list[Role]:
    user = await _get_user_or_404(db, user_id)
    try:
        await role_service.revoke_role(db, user, role_name)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LastRoleRemovalError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    await db.commit()
    return await role_service.get_user_roles(db, user)
