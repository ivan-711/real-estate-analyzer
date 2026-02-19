from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Fields for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Fields for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data returned in API responses (excludes password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: Optional[str]
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """JWT tokens returned by register, login, and refresh endpoints."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request body for refresh token endpoint."""

    refresh_token: str
