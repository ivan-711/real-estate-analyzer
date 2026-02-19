"""
Tests for Deal CRUD API endpoints.
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
    }


def _valid_deal_payload(property_id: str) -> dict:
    return {
        "property_id": property_id,
        "deal_name": "First Deal",
        "purchase_price": "250000",
        "gross_monthly_rent": "2200",
        "closing_costs": "5000",
        "down_payment_pct": "20",
        "interest_rate": "6.5",
        "loan_term_years": 30,
    }


# --- Happy path ---


async def test_create_deal_success(client: AsyncClient) -> None:
    """POST /api/v1/deals with valid property_id and data returns 201."""
    headers = await _auth_headers(client)
    prop = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    assert prop.status_code == 201
    property_id = prop.json()["id"]
    response = await client.post(
        "/api/v1/deals/",
        json=_valid_deal_payload(property_id),
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == property_id
    assert data["deal_name"] == "First Deal"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data
    # Calculated fields not implemented yet
    assert data.get("noi") is None
    assert data.get("cap_rate") is None


async def test_list_deals_success(client: AsyncClient) -> None:
    """GET /api/v1/deals returns 200 and list."""
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/deals/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_deals_filter_by_property_id(client: AsyncClient) -> None:
    """GET /api/v1/deals?property_id= returns only deals for that property."""
    headers = await _auth_headers(client)
    prop = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    property_id = prop.json()["id"]
    await client.post(
        "/api/v1/deals/",
        json=_valid_deal_payload(property_id),
        headers=headers,
    )
    response = await client.get(
        "/api/v1/deals/",
        params={"property_id": property_id},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(d["property_id"] == property_id for d in data)


async def test_get_deal_by_id_success(client: AsyncClient) -> None:
    """GET /api/v1/deals/{id} returns 200 and deal."""
    headers = await _auth_headers(client)
    prop = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    property_id = prop.json()["id"]
    create = await client.post(
        "/api/v1/deals/",
        json=_valid_deal_payload(property_id),
        headers=headers,
    )
    deal_id = create.json()["id"]
    response = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == deal_id
    assert response.json()["deal_name"] == "First Deal"


async def test_update_deal_success(client: AsyncClient) -> None:
    """PUT /api/v1/deals/{id} returns 200 and updated deal."""
    headers = await _auth_headers(client)
    prop = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    property_id = prop.json()["id"]
    create = await client.post(
        "/api/v1/deals/",
        json=_valid_deal_payload(property_id),
        headers=headers,
    )
    deal_id = create.json()["id"]
    response = await client.put(
        f"/api/v1/deals/{deal_id}",
        json={"deal_name": "Updated Deal", "gross_monthly_rent": "2400"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["deal_name"] == "Updated Deal"
    # Decimal may serialize as number or string (e.g. "2400.00")
    assert response.json()["gross_monthly_rent"] in (2400, 2400.0, "2400", "2400.00")


async def test_delete_deal_success(client: AsyncClient) -> None:
    """DELETE /api/v1/deals/{id} returns 204; then GET returns 404."""
    headers = await _auth_headers(client)
    prop = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers,
    )
    property_id = prop.json()["id"]
    create = await client.post(
        "/api/v1/deals/",
        json=_valid_deal_payload(property_id),
        headers=headers,
    )
    deal_id = create.json()["id"]
    response = await client.delete(f"/api/v1/deals/{deal_id}", headers=headers)
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_resp.status_code == 404


# --- Auth ---


async def test_create_deal_unauthenticated(client: AsyncClient) -> None:
    """POST /api/v1/deals without token returns 401."""
    response = await client.post(
        "/api/v1/deals/",
        json={
            "property_id": str(uuid.uuid4()),
            "purchase_price": "200000",
            "gross_monthly_rent": "2000",
        },
    )
    assert response.status_code == 401


async def test_list_deals_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/deals without token returns 401."""
    response = await client.get("/api/v1/deals/")
    assert response.status_code == 401


async def test_get_deal_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/deals/{id} without token returns 401."""
    response = await client.get(f"/api/v1/deals/{uuid.uuid4()}")
    assert response.status_code == 401


async def test_update_deal_unauthenticated(client: AsyncClient) -> None:
    """PUT /api/v1/deals/{id} without token returns 401."""
    response = await client.put(
        f"/api/v1/deals/{uuid.uuid4()}",
        json={"deal_name": "Hacked"},
    )
    assert response.status_code == 401


async def test_delete_deal_unauthenticated(client: AsyncClient) -> None:
    """DELETE /api/v1/deals/{id} without token returns 401."""
    response = await client.delete(f"/api/v1/deals/{uuid.uuid4()}")
    assert response.status_code == 401


# --- Validation ---


async def test_create_deal_invalid_body(client: AsyncClient) -> None:
    """POST with missing required fields returns 422."""
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/deals/",
        json={
            "property_id": str(uuid.uuid4()),
            # missing purchase_price, gross_monthly_rent
        },
        headers=headers,
    )
    assert response.status_code == 422


async def test_create_deal_property_not_found(client: AsyncClient) -> None:
    """POST with non-existent property_id returns 404 (property must exist and belong to user)."""
    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/deals/",
        json={
            "property_id": str(uuid.uuid4()),
            "purchase_price": "200000",
            "gross_monthly_rent": "2000",
        },
        headers=headers,
    )
    assert response.status_code == 404


# --- User isolation: User B must NOT see User A's deal ---


async def test_user_b_cannot_see_user_a_deal(client: AsyncClient) -> None:
    """Create deal as User A; User B cannot see it (GET 404, list does not include it)."""
    # User A: register, create property, create deal
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
    prop = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers_a,
    )
    property_id = prop.json()["id"]
    create = await client.post(
        "/api/v1/deals/",
        json=_valid_deal_payload(property_id),
        headers=headers_a,
    )
    assert create.status_code == 201
    deal_id = create.json()["id"]

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

    # User B GET deal by id -> 404
    get_resp = await client.get(f"/api/v1/deals/{deal_id}", headers=headers_b)
    assert get_resp.status_code == 404

    # User B list deals -> must not include A's deal
    list_resp = await client.get("/api/v1/deals/", headers=headers_b)
    assert list_resp.status_code == 200
    ids = [d["id"] for d in list_resp.json()]
    assert deal_id not in ids

    # User B PUT/DELETE -> 404
    put_resp = await client.put(
        f"/api/v1/deals/{deal_id}",
        json={"deal_name": "Hacked"},
        headers=headers_b,
    )
    assert put_resp.status_code == 404
    del_resp = await client.delete(f"/api/v1/deals/{deal_id}", headers=headers_b)
    assert del_resp.status_code == 404


async def test_user_b_cannot_create_deal_for_user_a_property(
    client: AsyncClient,
) -> None:
    """User B tries to create a deal with property_id owned by User A -> 404."""
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
    prop = await client.post(
        "/api/v1/properties/",
        json=_valid_property_payload(),
        headers=headers_a,
    )
    property_id = prop.json()["id"]

    # User B: register and try to create deal for A's property
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
    response = await client.post(
        "/api/v1/deals/",
        json=_valid_deal_payload(property_id),
        headers=headers_b,
    )
    assert response.status_code == 404
