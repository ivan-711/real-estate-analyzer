"""Pydantic schemas for chat sessions and messages."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    """Payload for sending a new message (user content only)."""

    message: str = Field(..., min_length=1, max_length=32000)
    session_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Existing session to continue; omit to create a new session.",
    )


class ChatMessageResponse(BaseModel):
    """A single chat message as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    referenced_deals: Optional[list[uuid.UUID]] = None
    referenced_properties: Optional[list[uuid.UUID]] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    created_at: datetime


class ChatSessionResponse(BaseModel):
    """A chat session with optional full message history."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = Field(default_factory=list)


class ChatSessionListItem(BaseModel):
    """Summary of a chat session for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChatSendResponse(BaseModel):
    """Response after sending a message (non-streaming fallback or metadata)."""

    session_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
