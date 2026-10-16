"""Pydantic schemas for user authentication and account management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from opentrace.core.normalization import normalize_email


class UserRegisterRequest(BaseModel):
    """User registration payload."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return normalize_email(v)


class UserLoginRequest(BaseModel):
    """User login payload."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return normalize_email(v)


class UserResponse(BaseModel):
    """Public user profile response."""

    id: str
    email: str
    name: str
    role: str
    is_active: bool
    preferences: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | str
    updated_at: datetime | str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "Bearer"
    user: UserResponse


class UserUpdateRequest(BaseModel):
    """Update profile request."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    preferences: dict[str, Any] | None = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    """Request password reset link."""

    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return normalize_email(v)


class ResetPasswordRequest(BaseModel):
    """Reset password using reset token."""

    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)
