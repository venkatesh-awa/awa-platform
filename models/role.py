"""Role-based access control: a normalized `roles` table plus a `user_roles`
join table that lets a user hold more than one role at once (e.g. a Seller
who also buys, or an Admin who is also an Accountant).

`users.primary_role_id` (models/user.py) is a real foreign key to `roles.id`
- not a free-text string - read by bid_service.REQUIRED_BID_ROLES, the seller
lookups in vehicle_intake_service, and the JWT `roles` claim. `user_roles` is
the source of truth for the full set of roles a user holds; a user's primary
role is always also one of their `user_roles` rows, kept that way by
services/role_service.assign_role/revoke_role. See alembic/versions/0029_roles
and 0030_users_primary_role_fk for the seed list, backfill, and the string
column -> FK migration.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Unicode, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.user import User


class Role(Base):
    """A named permission grouping. New roles should be added via an Alembic
    migration (not created ad hoc at runtime) since role names are referenced
    by string in application code, e.g. services/bid_service.REQUIRED_BID_ROLES.
    """

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Unicode(50), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Unicode(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class UserRole(Base):
    """One user<->role assignment (a user may hold several). Which one is
    "the" primary role is tracked on `users.primary_role_id`, not here -
    keeping that single-valued fact in one place avoids the two ever
    disagreeing. "Every user has at least one role" is enforced by the 0029
    migration's backfill plus services/role_service.revoke_role refusing to
    remove a user's last row, rather than a DB constraint - SQL Server has no
    portable way to require "at least one matching child row exists" without
    a trigger.
    """

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="user_roles")
