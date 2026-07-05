"""Request/response schemas for the local authentication API.

Password strength is enforced here (at the edge) so invalid input is rejected
with a 422 before ever reaching the service or the hasher.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Minimum policy: 8-72 chars with at least one letter and one digit. The 72-byte
# ceiling keeps inputs within Argon2-friendly bounds and blocks trivial DoS via
# multi-megabyte passwords.
_PASSWORD_MIN = 8
_PASSWORD_MAX = 72
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def _validate_password(value: str) -> str:
    if not (_PASSWORD_MIN <= len(value) <= _PASSWORD_MAX):
        raise ValueError(f"Password must be between {_PASSWORD_MIN} and {_PASSWORD_MAX} characters")
    if not _HAS_LETTER.search(value) or not _HAS_DIGIT.search(value):
        raise ValueError("Password must contain at least one letter and one digit")
    return value


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=_PASSWORD_MIN, max_length=_PASSWORD_MAX)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password(v)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=_PASSWORD_MAX)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class SignOutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=_PASSWORD_MIN, max_length=_PASSWORD_MAX)

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password(v)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access-token lifetime in seconds


class MessageResponse(BaseModel):
    message: str


class UserRead(BaseModel):
    """Built explicitly via services.auth_service.to_user_read, not
    model_validate(user) - User has no `role`/`roles` attributes (see
    models/user.py's primary_role_id/primary_role + models/role.py's
    user_roles), so from_attributes can't populate these fields on its own.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: str
    roles: list[str]
    is_email_verified: bool
    created_at: datetime
