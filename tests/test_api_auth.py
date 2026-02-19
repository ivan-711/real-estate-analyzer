"""
Tests for JWT authentication API endpoints.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


def _unique_email() -> str:
    """Generate a unique email for test isolation."""
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def test_register_success(client: TestClient) -> None:
    """POST valid UserCreate returns 201 with access_token and refresh_token."""
    response = client.post(
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


def test_register_duplicate_email(client: TestClient) -> None:
    """Register same email twice returns 400 on second attempt."""
    email = _unique_email()
    payload = {
        "email": email,
        "password": "password123",
        "full_name": "First User",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400
    data = second.json()
    assert "Email already registered" in str(data.get("detail", data))


def test_register_invalid_email(client: TestClient) -> None:
    """Invalid email format returns 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test",
        },
    )
    assert response.status_code == 422


def test_register_short_password(client: TestClient) -> None:
    """Password shorter than 8 chars returns 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpw@example.com",
            "password": "short",
            "full_name": "Test",
        },
    )
    assert response.status_code == 422


def test_login_success(client: TestClient) -> None:
    """POST valid credentials returns 200 with tokens."""
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Login User",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_password(client: TestClient) -> None:
    """Wrong password returns 401."""
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "User",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_email(client: TestClient) -> None:
    """Unknown email returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 401


def test_refresh_success(client: TestClient) -> None:
    """POST valid refresh_token returns 200 with new access_token."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": _unique_email(),
            "password": "password123",
            "full_name": "Refresh User",
        },
    )
    refresh_token = reg.json()["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] != reg.json()["access_token"]


def test_refresh_invalid_token(client: TestClient) -> None:
    """Invalid or expired refresh token returns 401."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code == 401


def test_me_authenticated(client: TestClient) -> None:
    """GET /me with valid Bearer returns 200 with UserResponse."""
    email = _unique_email()
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Me User",
        },
    )
    access_token = reg.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "Me User"
    assert "id" in data
    assert "password_hash" not in data


def test_me_unauthenticated(client: TestClient) -> None:
    """GET /me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_invalid_token(client: TestClient) -> None:
    """GET /me with invalid Bearer returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
