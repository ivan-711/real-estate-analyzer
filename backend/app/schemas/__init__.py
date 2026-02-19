"""Pydantic request/response schemas."""

from __future__ import annotations

from app.schemas.deal import DealCreate, DealResponse, DealUpdate
from app.schemas.property import PropertyCreate, PropertyResponse, PropertyUpdate
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "DealCreate",
    "DealUpdate",
    "DealResponse",
]
