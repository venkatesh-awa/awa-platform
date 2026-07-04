"""Response schemas for the admin dashboard chrome (sidebar + section card
grids). Same single-localized-field convention as schemas/content.py."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class AdminNavItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parent_id: uuid.UUID | None
    label: str
    icon_class: str | None
    url: str
    sort_order: int = 0


class AdminDashboardCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_key: str
    label: str
    description: str | None
    icon_class: str | None
    url: str
    image_url: str | None
    sort_order: int = 0
