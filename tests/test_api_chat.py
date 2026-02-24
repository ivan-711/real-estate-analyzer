"""Tests for the chat API endpoints (POST /chat, sessions CRUD)."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_sse(body: str) -> list[dict]:
    """Parse an SSE response body into a list of {event, data} dicts."""
    events: list[dict] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_name = ""
        data_value = ""
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_name = line[len("event: ") :]
            elif line.startswith("data: "):
                data_value = line[len("data: ") :]
        if event_name or data_value:
            events.append({"event": event_name, "data": data_value})
    return events


def _build_anthropic_mock() -> MagicMock:
    """Return a patched AsyncAnthropic whose messages.stream() yields chunks."""
    chunks = ["Hello", " from", " the", " AI"]

    mock_stream = AsyncMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)

    async def _text_stream():
        for c in chunks:
            yield c

    mock_stream.text_stream = _text_stream()

    mock_final = MagicMock()
    mock_final.usage.input_tokens = 50
    mock_final.usage.output_tokens = 20
    mock_stream.get_final_message = MagicMock(return_value=mock_final)

    mock_client = MagicMock()
    mock_client.messages.stream = MagicMock(return_value=mock_stream)

    mock_cls = MagicMock(return_value=mock_client)
    return mock_cls


def _fresh_anthropic_mock() -> MagicMock:
    """Build a new mock each time (text_stream is consumed once per call)."""
    return _build_anthropic_mock()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

CHAT_URL = "/api/v1/chat"
SESSIONS_URL = "/api/v1/chat/sessions"


@patch(
    "app.services.chatbot.anthropic.AsyncAnthropic", new_callable=_fresh_anthropic_mock
)
async def test_send_message_creates_session(
    mock_anthropic, client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """POST /chat with no session_id creates a new session and streams SSE."""
    response = await client.post(
        CHAT_URL,
        json={"message": "Hello AI"},
        headers=auth_headers,
    )
    assert response.status_code == 200

    events = parse_sse(response.text)
    chunk_events = [e for e in events if e["event"] == "chunk"]
    done_events = [e for e in events if e["event"] == "done"]

    assert len(chunk_events) >= 1
    assert len(done_events) == 1

    done_data = json.loads(done_events[0]["data"])
    assert "session_id" in done_data
    assert "user_message_id" in done_data
    assert "assistant_message_id" in done_data

    session_id = done_data["session_id"]
    session_resp = await client.get(
        f"{SESSIONS_URL}/{session_id}",
        headers=auth_headers,
    )
    assert session_resp.status_code == 200


@patch(
    "app.services.chatbot.anthropic.AsyncAnthropic", new_callable=_fresh_anthropic_mock
)
async def test_send_message_existing_session(
    mock_anthropic, client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """Send two messages to the same session; both appear in history."""
    # First message creates a session
    r1 = await client.post(
        CHAT_URL, json={"message": "First message"}, headers=auth_headers
    )
    assert r1.status_code == 200
    done1 = json.loads(
        [e for e in parse_sse(r1.text) if e["event"] == "done"][0]["data"]
    )
    session_id = done1["session_id"]

    # Need a fresh mock for the second call (text_stream is consumed)
    with patch(
        "app.services.chatbot.anthropic.AsyncAnthropic",
        new_callable=_fresh_anthropic_mock,
    ):
        r2 = await client.post(
            CHAT_URL,
            json={"message": "Second message", "session_id": session_id},
            headers=auth_headers,
        )
    assert r2.status_code == 200

    # Verify history
    session_resp = await client.get(
        f"{SESSIONS_URL}/{session_id}", headers=auth_headers
    )
    assert session_resp.status_code == 200
    messages = session_resp.json()["messages"]
    assert len(messages) == 4  # user + assistant + user + assistant


async def test_send_message_unauthenticated(client: AsyncClient) -> None:
    """POST /chat without auth returns 401."""
    response = await client.post(CHAT_URL, json={"message": "Hello"})
    assert response.status_code == 401


@patch(
    "app.services.chatbot.anthropic.AsyncAnthropic", new_callable=_fresh_anthropic_mock
)
async def test_send_message_invalid_session(
    mock_anthropic, client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """POST /chat with a nonexistent session_id returns 404."""
    response = await client.post(
        CHAT_URL,
        json={"message": "Hello", "session_id": str(uuid.uuid4())},
        headers=auth_headers,
    )
    assert response.status_code == 404


@patch(
    "app.services.chatbot.anthropic.AsyncAnthropic", new_callable=_fresh_anthropic_mock
)
async def test_list_sessions(
    mock_anthropic, client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """Create two sessions, verify both returned newest first."""
    r1 = await client.post(
        CHAT_URL, json={"message": "Session one"}, headers=auth_headers
    )
    assert r1.status_code == 200
    sid1 = json.loads(
        [e for e in parse_sse(r1.text) if e["event"] == "done"][0]["data"]
    )["session_id"]

    with patch(
        "app.services.chatbot.anthropic.AsyncAnthropic",
        new_callable=_fresh_anthropic_mock,
    ):
        r2 = await client.post(
            CHAT_URL, json={"message": "Session two"}, headers=auth_headers
        )
    assert r2.status_code == 200
    sid2 = json.loads(
        [e for e in parse_sse(r2.text) if e["event"] == "done"][0]["data"]
    )["session_id"]

    list_resp = await client.get(SESSIONS_URL, headers=auth_headers)
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    session_ids = [s["id"] for s in sessions]
    assert sid1 in session_ids
    assert sid2 in session_ids
    assert len(sessions) >= 2
    # Newest first: sid2 should precede sid1
    assert session_ids.index(sid2) < session_ids.index(sid1)


@patch(
    "app.services.chatbot.anthropic.AsyncAnthropic", new_callable=_fresh_anthropic_mock
)
async def test_get_session_with_messages(
    mock_anthropic, client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """GET /sessions/{id} returns the session with full message history."""
    r = await client.post(
        CHAT_URL, json={"message": "Tell me about my deals"}, headers=auth_headers
    )
    assert r.status_code == 200
    done = json.loads([e for e in parse_sse(r.text) if e["event"] == "done"][0]["data"])
    session_id = done["session_id"]

    session_resp = await client.get(
        f"{SESSIONS_URL}/{session_id}", headers=auth_headers
    )
    assert session_resp.status_code == 200
    data = session_resp.json()
    assert data["id"] == session_id
    assert len(data["messages"]) == 2  # user + assistant
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"


async def test_get_session_not_found(
    client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """GET /sessions/{random_uuid} returns 404."""
    response = await client.get(f"{SESSIONS_URL}/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


@patch(
    "app.services.chatbot.anthropic.AsyncAnthropic", new_callable=_fresh_anthropic_mock
)
async def test_delete_session(
    mock_anthropic, client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """DELETE a session, verify 204, then GET returns 404."""
    r = await client.post(
        CHAT_URL, json={"message": "To be deleted"}, headers=auth_headers
    )
    assert r.status_code == 200
    done = json.loads([e for e in parse_sse(r.text) if e["event"] == "done"][0]["data"])
    session_id = done["session_id"]

    del_resp = await client.request(
        "DELETE", f"{SESSIONS_URL}/{session_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{SESSIONS_URL}/{session_id}", headers=auth_headers)
    assert get_resp.status_code == 404

    list_resp = await client.get(SESSIONS_URL, headers=auth_headers)
    session_ids = [s["id"] for s in list_resp.json()]
    assert session_id not in session_ids


@patch(
    "app.services.chatbot.anthropic.AsyncAnthropic", new_callable=_fresh_anthropic_mock
)
async def test_session_isolation(
    mock_anthropic, client: AsyncClient, auth_headers: dict, test_user, create_user
) -> None:
    """User A's session is invisible to User B."""
    # User A creates a session
    r = await client.post(
        CHAT_URL, json={"message": "User A message"}, headers=auth_headers
    )
    assert r.status_code == 200
    done = json.loads([e for e in parse_sse(r.text) if e["event"] == "done"][0]["data"])
    session_id_a = done["session_id"]

    # Create User B
    _, _, headers_b = await create_user(email="userb@example.com", full_name="User B")

    # User B cannot GET User A's session
    resp = await client.get(f"{SESSIONS_URL}/{session_id_a}", headers=headers_b)
    assert resp.status_code == 404

    # User B's session list does not include User A's session
    list_resp = await client.get(SESSIONS_URL, headers=headers_b)
    assert list_resp.status_code == 200
    session_ids_b = [s["id"] for s in list_resp.json()]
    assert session_id_a not in session_ids_b


async def test_send_message_empty_body(
    client: AsyncClient, auth_headers: dict, test_user
) -> None:
    """POST with empty or missing message returns 422."""
    # Empty message
    r1 = await client.post(CHAT_URL, json={"message": ""}, headers=auth_headers)
    assert r1.status_code == 422

    # Missing message field
    r2 = await client.post(CHAT_URL, json={}, headers=auth_headers)
    assert r2.status_code == 422
