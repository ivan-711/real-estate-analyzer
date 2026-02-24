"""Chatbot service: LLM prompt engineering and context injection.

This module is DEVELOPER-OWNED. The implementation below is a minimal stub
so the chat router can run end-to-end. The developer will replace it with
real prompt engineering, deal serialization, and context injection.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

# Stub: async generator that yields placeholder text chunks.
# Replace with real Claude API streaming + context injection.


async def stream_chat_response(
    user_id: uuid.UUID,
    message: str,
    history: list[dict[str, Any]],
) -> AsyncIterator[str]:
    """Stream assistant response chunks for the given user message and session history.

    Args:
        user_id: Current user (for loading their deals into context; stub ignores).
        message: The user's latest message.
        history: Previous messages in the session, each with 'role' and 'content'.

    Yields:
        Text chunks to send to the client (SSE). The developer's implementation
        will stream from the LLM and may yield token usage or metadata at the end.
    """
    # Stub: yield a placeholder response in chunks so streaming is exercised.
    del user_id, history  # unused in stub
    placeholder = (
        f"You said: \"{message[:100]}{'...' if len(message) > 100 else ''}\". "
        "This is a placeholder response from the chatbot stub. "
        "Replace this with real LLM prompt engineering and context injection in "
        "backend/app/services/chatbot.py."
    )
    # Simulate chunked streaming
    chunk_size = 20
    for i in range(0, len(placeholder), chunk_size):
        yield placeholder[i : i + chunk_size]
