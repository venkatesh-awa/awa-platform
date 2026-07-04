"""Admin dashboard chrome: the sidebar sections and the action-card grids
shown within each section (e.g. the Sellers grid: Add a New Car, My Vehicles,
...). Kept separate from models/content.py's public menu_items tree since
this is a distinct, authenticated-only navigation surface with its own shape
(cards are grouped by `section_key`, not a parent/child tree).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Unicode, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AdminNavItem(Base):
    """One entry in the admin sidebar (Home, Sellers, Operations, ...).

    `parent_id` supports one level of nesting (e.g. Admin -> Dashboard, In
    Store), same self-referencing pattern as models/content.py's MenuItem.
    """

    __tablename__ = "admin_nav_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # NO ACTION (not CASCADE): SQL Server rejects a self-referencing FK with a
    # cascade path since a delete could cycle back to the same table.
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("admin_nav_items.id", ondelete="NO ACTION"), nullable=True
    )
    label_en: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    label_ar: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    icon_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class AdminDashboardCard(Base):
    """One action tile within a sidebar section's landing grid. `section_key`
    groups cards by which sidebar item they belong to (e.g. "sellers",
    "dashboard") - a section with no cards yet simply returns an empty list."""

    __tablename__ = "admin_dashboard_cards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    label_en: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    label_ar: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    description_en: Mapped[str | None] = mapped_column(Unicode(300), nullable=True)
    description_ar: Mapped[str | None] = mapped_column(Unicode(300), nullable=True)
    icon_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
