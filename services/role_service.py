"""Role assignment: manages the normalized roles/user_roles tables
(models/role.py) and keeps `users.primary_role_id` pointed at one of a
user's own `user_roles` rows.

Every user must hold at least one role. The 0029_roles migration guarantees
that for users that already existed; `revoke_role` guarantees it going
forward by refusing to remove a user's last role.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.role import Role, UserRole
from models.user import User
from services.exceptions import LastRoleRemovalError, RoleNotFoundError


async def list_roles(db: AsyncSession, *, active_only: bool = True) -> list[Role]:
    query = select(Role)
    if active_only:
        query = query.where(Role.is_active)
    result = await db.execute(query.order_by(Role.name))
    return list(result.scalars().all())


async def get_role_by_name(db: AsyncSession, name: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if role is None:
        raise RoleNotFoundError(name)
    return role


async def get_user_roles(db: AsyncSession, user: User) -> list[Role]:
    result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
        .order_by(Role.name)
    )
    return list(result.scalars().all())


async def assign_role(db: AsyncSession, user: User, role_name: str, *, is_primary: bool = False) -> UserRole:
    """Grant `role_name` to `user`. Idempotent - assigning a role the user
    already holds just returns the existing row. When `is_primary` is set,
    points `users.primary_role_id` at this role.

    Does not commit; callers own the transaction (see auth_service.sign_up
    for the pattern of flush-then-commit-once)."""
    role = await get_role_by_name(db, role_name)

    result = await db.execute(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id))
    user_role = result.scalar_one_or_none()
    if user_role is None:
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)

    if is_primary:
        user.primary_role_id = role.id
        user.primary_role = role  # avoid a lazy-load if read back before a refresh

    await db.flush()
    return user_role


async def revoke_role(db: AsyncSession, user: User, role_name: str) -> None:
    """Revoke `role_name` from `user`. Raises LastRoleRemovalError rather than
    leaving a user with zero roles. If the revoked role was the primary one,
    the longest-held remaining role is promoted to primary.

    Does not commit; callers own the transaction."""
    role = await get_role_by_name(db, role_name)

    result = await db.execute(select(UserRole).where(UserRole.user_id == user.id))
    current = list(result.scalars().all())
    target = next((ur for ur in current if ur.role_id == role.id), None)
    if target is None:
        return

    if len(current) == 1:
        raise LastRoleRemovalError(user.id)

    was_primary = user.primary_role_id == role.id
    await db.delete(target)
    await db.flush()

    if was_primary:
        remaining = [ur for ur in current if ur.id != target.id]
        promoted = min(remaining, key=lambda ur: ur.assigned_at)
        promoted_role = await db.get(Role, promoted.role_id)
        assert promoted_role is not None
        user.primary_role_id = promoted_role.id
        user.primary_role = promoted_role
        await db.flush()
