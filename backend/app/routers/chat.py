"""Chat API: send message (streaming SSE), list/get/delete sessions."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionListItem,
    ChatSessionResponse,
)
from app.services.chatbot import stream_chat_response
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _sse_event(event: str, data: str) -> str:
    """Format one SSE event (event name + data payload)."""
    return f"event: {event}\ndata: {data}\n\n"


async def _stream_send(
    user: User,
    body: ChatMessageCreate,
    db: AsyncSession,
) -> AsyncIterator[str]:
    """Get or create session, save user message, stream assistant response, save assistant message; yield SSE events."""
    session_id = body.session_id
    if session_id is not None:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        title = (
            (body.message[:197] + "...") if len(body.message) > 200 else body.message
        )
        session = ChatSession(user_id=user.id, title=title or "New chat")
        db.add(session)
        await db.flush()

    # Load existing messages for history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    existing = result.scalars().all()
    history = [{"role": m.role, "content": m.content} for m in existing]

    # Persist user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.flush()

    # Stream assistant response and accumulate content
    full_content: list[str] = []
    async for chunk in stream_chat_response(user.id, body.message, history, db):
        full_content.append(chunk)
        # SSE: send chunk (escape newlines in data)
        payload = json.dumps({"text": chunk})
        yield _sse_event("chunk", payload)

    assistant_content = "".join(full_content)
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=assistant_content,
        input_tokens=None,
        output_tokens=None,
    )
    db.add(assistant_msg)
    await db.flush()

    # Bump session updated_at so list order reflects latest activity
    session.updated_at = datetime.utcnow()
    await db.commit()

    # Final SSE event with ids
    done_data = json.dumps(
        {
            "session_id": str(session.id),
            "user_message_id": str(user_msg.id),
            "assistant_message_id": str(assistant_msg.id),
        }
    )
    yield _sse_event("done", done_data)


@router.post("")
async def send_message(
    body: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Send a message and stream the AI response via Server-Sent Events.

    Events: `chunk` (data: {"text": "..."}), then `done` (data: {"session_id", "user_message_id", "assistant_message_id"}).
    Creates a new session if session_id is omitted.
    """
    return StreamingResponse(
        _stream_send(current_user, body, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=list[ChatSessionListItem])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSessionListItem]:
    """List the current user's chat sessions (newest first)."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [ChatSessionListItem.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    """Get a chat session with full message history. Scoped to current user."""
    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[ChatMessageResponse.model_validate(m) for m in session.messages],
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a chat session and all its messages. Scoped to current user."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    await db.delete(session)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
