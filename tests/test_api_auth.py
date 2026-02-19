"""
Tests for JWT authentication API endpoints.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient


def _unique_email() -> str:
    """Generate a unique email for test isolation."""
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


async def test_register_success(client: AsyncClient) -> None:
    """POST valid UserCreate returns 201 with access_token and refresh_token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": _unique_email(),
            "password": "password123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Register same email twice returns 400 on second attempt."""
    email = _unique_email()
    payload = {
        "email": email,
        "password": "password123",
        "full_name": "First User",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400
    data = second.json()
    assert "Email already registered" in str(data.get("detail", data))


async def test_register_invalid_email(client: AsyncClient) -> None:
    """Invalid email format returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test",
        },
    )
    assert response.status_code == 422


async def test_register_short_password(client: AsyncClient) -> None:
    """Password shorter than 8 chars returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpw@example.com",
            "password": "short",
            "full_name": "Test",
        },
    )
    assert response.status_code == 422


async def test_login_success(client: AsyncClient) -> None:
    """POST valid credentials returns 200 with tokens."""
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Login User",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_invalid_password(client: AsyncClient) -> None:
    """Wrong password returns 401."""
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "User",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient) -> None:
    """Unknown email returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 401


async def test_refresh_success(client: AsyncClient) -> None:
    """POST valid refresh_token returns 200 with new access_token."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": _unique_email(),
            "password": "password123",
            "full_name": "Refresh User",
        },
    )
    refresh_token = reg.json()["refresh_token"]
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] != reg.json()["access_token"]


async def test_refresh_invalid_token(client: AsyncClient) -> None:
    """Invalid or expired refresh token returns 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code == 401


async def test_me_authenticated(client: AsyncClient) -> None:
    """GET /me with valid Bearer returns 200 with UserResponse."""
    email = _unique_email()
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Me User",
        },
    )
    access_token = reg.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "Me User"
    assert "id" in data
    assert "password_hash" not in data


async def test_me_unauthenticated(client: AsyncClient) -> None:
    """GET /me without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_invalid_token(client: AsyncClient) -> None:
    """GET /me with invalid Bearer returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
