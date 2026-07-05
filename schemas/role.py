"""Request/response schemas for role assignment (services/role_service.py)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None


class UserRoleAssignRequest(BaseModel):
    role_name: str = Field(min_length=1, max_length=50)
    is_primary: bool = False
