"""
Tests for Property CRUD API endpoints.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a user and return Authorization headers."""
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _valid_property_payload() -> dict:
    return {
        "address": "123 Main St",
        "city": "Cleveland",
        "state": "OH",
        "zip_code": "44101",
        "property_type": "single_family",
        "num_units": 1,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "square_footage": 1500,
        "year_built": 1990,
    }


# --- Happy path ---


async def test_create_property_success(client: AsyncClient) -> None:
    """POST /api/v1/properties with valid data returns 201 and property."""
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["address"] == "123 Main St"
    assert data["city"] == "Cleveland"
    assert data["state"] == "OH"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "user_id" in data


async def test_list_properties_success(client: AsyncClient) -> None:
    """GET /api/v1/properties returns 200 and list (paginated)."""
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/properties/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_get_property_by_id_success(client: AsyncClient) -> None:
    """GET /api/v1/properties/{id} returns 200 and property."""
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    assert create.status_code == 201
    prop_id = create.json()["id"]
    response = await client.get(f"/api/v1/properties/{prop_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == prop_id
    assert response.json()["address"] == "123 Main St"


async def test_update_property_success(client: AsyncClient) -> None:
    """PUT /api/v1/properties/{id} returns 200 and updated property."""
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    prop_id = create.json()["id"]
    response = await client.put(
        f"/api/v1/properties/{prop_id}",
        json={"city": "Columbus", "state": "OH"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["city"] == "Columbus"
    assert response.json()["address"] == "123 Main St"


async def test_delete_property_success(client: AsyncClient) -> None:
    """DELETE /api/v1/properties/{id} returns 204; then GET returns 404."""
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    prop_id = create.json()["id"]
    response = await client.delete(f"/api/v1/properties/{prop_id}", headers=headers)
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/properties/{prop_id}", headers=headers)
    assert get_resp.status_code == 404


async def test_property_lookup_placeholder(client: AsyncClient) -> None:
    """POST /api/v1/properties/lookup returns 200 with placeholder message."""
    headers = await _auth_headers(client)
    response = await client.post("/api/v1/properties/lookup", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


# --- Auth ---


async def test_create_property_unauthenticated(client: AsyncClient) -> None:
    """POST /api/v1/properties without token returns 401."""
    response = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
    )
    assert response.status_code == 401


async def test_list_properties_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/properties without token returns 401."""
    response = await client.get("/api/v1/properties/")
    assert response.status_code == 401


async def test_get_property_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/properties/{id} without token returns 401."""
    response = await client.get(f"/api/v1/properties/{uuid.uuid4()}")
    assert response.status_code == 401


async def test_update_property_unauthenticated(client: AsyncClient) -> None:
    """PUT /api/v1/properties/{id} without token returns 401."""
    response = await client.put(
        f"/api/v1/properties/{uuid.uuid4()}",
        json={"city": "Columbus"},
    )
    assert response.status_code == 401


async def test_delete_property_unauthenticated(client: AsyncClient) -> None:
    """DELETE /api/v1/properties/{id} without token returns 401."""
    response = await client.delete(f"/api/v1/properties/{uuid.uuid4()}")
    assert response.status_code == 401


# --- Validation ---


async def test_create_property_invalid_body(client: AsyncClient) -> None:
    """POST with invalid/missing required fields returns 422."""
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/properties/",
        json={
            "address": "123 Main",
            # missing city, state, zip_code, property_type, num_units
        },
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_property_invalid_state_length(client: AsyncClient) -> None:
    """POST with state not 2 chars returns 422."""
    headers = await _auth_headers(client)
    payload = _valid_property_payload()
    payload["state"] = "OHIO"
    response = await client.post("/api/v1/properties/", json=payload, headers=headers)
    assert response.status_code == 422


# --- User isolation: User B must NOT see User A's property ---


async def test_user_b_cannot_see_user_a_property(client: AsyncClient) -> None:
    """Create property as User A; User B cannot see it (GET returns 404, list does not include it)."""
    # User A: register and create property
    email_a = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email_a,
            "password": "password123",
            "full_name": "User A",
        },
    )
    login_a = await client.post(
        "/api/v1/auth/login",
        json={"email": email_a, "password": "password123"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
    create = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers_a,
    )
    assert create.status_code == 201
    prop_id = create.json()["id"]

    # User B: register
    email_b = _unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email_b,
            "password": "password123",
            "full_name": "User B",
        },
    )
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": email_b, "password": "password123"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # User B GET property by id -> 404 (must not see it)
    get_resp = await client.get(f"/api/v1/properties/{prop_id}", headers=headers_b)
    assert get_resp.status_code == 404

    # User B list properties -> must not include A's property
    list_resp = await client.get("/api/v1/properties/", headers=headers_b)
    assert list_resp.status_code == 200
    ids = [p["id"] for p in list_resp.json()]
    assert prop_id not in ids

    # User B PUT/DELETE -> 404
    put_resp = await client.put(
        f"/api/v1/properties/{prop_id}",
        json={"city": "Hacked"},
        headers=headers_b,
    )
    assert put_resp.status_code == 404
    del_resp = await client.delete(f"/api/v1/properties/{prop_id}", headers=headers_b)
    assert del_resp.status_code == 404
