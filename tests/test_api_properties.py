"""
Tests for Property CRUD API endpoints.
"""

from __future__ import annotations

import uuid
from typing import Dict

from httpx import AsyncClient


async def test_create_property_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sheboygan_property_payload: dict,
) -> None:
    """POST /api/v1/properties with valid data returns 201 and property."""
    response = await client.post(
        "/api/v1/properties/",
        json=sheboygan_property_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["address"] == "1515 N 7th St"
    assert data["city"] == "Sheboygan"
    assert data["state"] == "WI"
    assert data["zip_code"] == "53081"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "user_id" in data


async def test_list_properties_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """GET /api/v1/properties returns 200 and list (paginated)."""
    response = await client.get("/api/v1/properties/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["id"] == str(test_property.id) for item in data)


async def test_get_property_by_id_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """GET /api/v1/properties/{id} returns 200 and property."""
    response = await client.get(
        f"/api/v1/properties/{test_property.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(test_property.id)
    assert response.json()["address"] == "1515 N 7th St"


async def test_update_property_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """PUT /api/v1/properties/{id} returns 200 and updated property."""
    response = await client.put(
        f"/api/v1/properties/{test_property.id}",
        json={"city": "Milwaukee", "state": "WI"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["city"] == "Milwaukee"
    assert response.json()["address"] == "1515 N 7th St"


async def test_delete_property_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """DELETE /api/v1/properties/{id} returns 204; then GET returns 404."""
    response = await client.delete(
        f"/api/v1/properties/{test_property.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
    get_resp = await client.get(
        f"/api/v1/properties/{test_property.id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 404


async def test_property_lookup_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    monkeypatch,
    sample_rentcast_property_response: Dict[str, object],
) -> None:
    """POST /api/v1/properties/lookup returns normalized property + rent estimate."""
    from app.integrations.rentcast import RentCastClient

    async def fake_lookup_property(self, address: str) -> dict:
        payload = dict(sample_rentcast_property_response)
        payload["address"] = address.split(",")[0].strip()
        return payload

    async def fake_get_rent_estimate(self, address: str) -> dict:
        return {
            "rent_estimate_monthly": 1800,
            "rent_estimate_low": 1650,
            "rent_estimate_high": 1950,
            "rent_estimate_confidence": 0.84,
        }

    monkeypatch.setattr(RentCastClient, "lookup_property", fake_lookup_property)
    monkeypatch.setattr(RentCastClient, "get_rent_estimate", fake_get_rent_estimate)

    response = await client.post(
        "/api/v1/properties/lookup",
        json={"address": "1515 N 7th St, Sheboygan, WI 53081"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "1515 N 7th St"
    assert data["city"] == "Sheboygan"
    assert data["state"] == "WI"
    assert data["zip_code"] == "53081"
    assert data["property_type"] == "duplex"
    assert data["bedrooms"] == 5
    assert data["bathrooms"] == 2.0
    assert data["square_footage"] == 2330
    assert data["year_built"] == 1900
    assert data["rent_estimate_monthly"] == 1800


async def test_property_sample_data_endpoint(
    client: AsyncClient,
    sample_rentcast_property_response: Dict[str, object],
) -> None:
    """GET /api/v1/properties/sample-data returns hardcoded sample lookup payload."""
    response = await client.get("/api/v1/properties/sample-data")
    assert response.status_code == 200
    assert response.json() == sample_rentcast_property_response


async def test_create_property_unauthenticated(
    client: AsyncClient,
    sheboygan_property_payload: dict,
) -> None:
    """POST /api/v1/properties without token returns 401."""
    response = await client.post(
        "/api/v1/properties/",
        json=sheboygan_property_payload,
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


async def test_create_property_invalid_body(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST with invalid/missing required fields returns 422."""
    response = await client.post(
        "/api/v1/properties/",
        json={
            "address": "1515 N 7th St",
            # missing city, state, zip_code, property_type, num_units
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_create_property_invalid_state_length(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sheboygan_property_payload: dict,
) -> None:
    """POST with state not 2 chars returns 422."""
    payload = dict(sheboygan_property_payload)
    payload["state"] = "WISC"
    response = await client.post(
        "/api/v1/properties/", json=payload, headers=auth_headers
    )
    assert response.status_code == 422


async def test_user_b_cannot_see_user_a_property(
    client: AsyncClient,
    test_property,
    create_user,
) -> None:
    """Create property as User A; User B cannot see it (GET 404, list excludes it)."""
    _, _, headers_b = await create_user(full_name="User B")

    get_resp = await client.get(
        f"/api/v1/properties/{test_property.id}", headers=headers_b
    )
    assert get_resp.status_code == 404

    list_resp = await client.get("/api/v1/properties/", headers=headers_b)
    assert list_resp.status_code == 200
    ids = [p["id"] for p in list_resp.json()]
    assert str(test_property.id) not in ids

    put_resp = await client.put(
        f"/api/v1/properties/{test_property.id}",
        json={"city": "Hacked"},
        headers=headers_b,
    )
    assert put_resp.status_code == 404

    del_resp = await client.delete(
        f"/api/v1/properties/{test_property.id}", headers=headers_b
    )
    assert del_resp.status_code == 404
