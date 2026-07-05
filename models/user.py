"""Local identity models: users plus the three single-use / rotating token
tables backing the sign-in, password-reset, and email-verification flows.

SQL Server is the source of truth (see models/auction.py header). Only the
*hash* of every refresh / reset / verification token is persisted - never the
raw value - so a database compromise cannot be replayed against the auth API.
Emails are stored lower-cased with a unique index; SQL Server's default
collation is case-insensitive, but lower-casing on write keeps the invariant
explicit and portable.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.auction import Bid
    from models.content import VehicleListing
    from models.role import Role, UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    last_name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # The role embedded in issued access tokens and read by single-role checks
    # (bid_service.REQUIRED_BID_ROLES, vehicle_intake_service's seller lookups).
    # A real FK, not a free-text string - see models/role.py. `user_roles` below
    # holds the full set of roles a user has; this is the one mirrored as
    # "the" role for callers that only care about one. lazy="joined" so it's
    # always populated alongside the user in a single query (no separate
    # async lazy-load needed at every read site).
    primary_role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    primary_role: Mapped[Role] = relationship(foreign_keys=[primary_role_id], lazy="joined")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Brute-force protection counters (see services/auth_service.sign_in).
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    email_verification_tokens: Mapped[list[EmailVerificationToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    bids: Mapped[list[Bid]] = relationship(back_populates="bidder")
    vehicle_listings: Mapped[list[VehicleListing]] = relationship(
        back_populates="seller", foreign_keys="[VehicleListing.seller_id]"
    )
    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    """A rotating, long-lived session token. Sign-in issues one; using it on
    /auth/refresh revokes the old row and issues a new one (rotation), so a
    stolen-and-replayed refresh token is detectable and short-lived."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="password_reset_tokens")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="email_verification_tokens")
