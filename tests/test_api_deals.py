"""
Tests for Deal CRUD API endpoints.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

from httpx import AsyncClient


def _preview_payload() -> dict:
    """Payload for guest preview (no property_id, no auth)."""
    return {
        "purchase_price": "220000",
        "gross_monthly_rent": "1700",
        "down_payment_pct": "20",
        "interest_rate": "7",
        "loan_term_years": 30,
        "vacancy_rate_pct": "5",
        "property_tax_monthly": "300",
        "insurance_monthly": "120",
        "maintenance_rate_pct": "5",
        "management_fee_pct": "10",
        "closing_costs": "0",
        "rehab_costs": "0",
        "hoa_monthly": "0",
        "utilities_monthly": "0",
    }


def _deal_payload_for_property(property_id: str) -> dict:
    return {
        "property_id": property_id,
        "deal_name": "Sheboygan Duplex Deal",
        "purchase_price": "220000",
        "closing_costs": "6600",
        "rehab_costs": "5000",
        "down_payment_pct": "20",
        "loan_amount": "176000",
        "interest_rate": "7.0",
        "loan_term_years": 30,
        "monthly_mortgage": "1171",
        "gross_monthly_rent": "1800",
        "other_monthly_income": "0",
        "property_tax_monthly": "320",
        "insurance_monthly": "120",
        "vacancy_rate_pct": "5",
        "maintenance_rate_pct": "5",
        "management_fee_pct": "10",
        "hoa_monthly": "0",
        "utilities_monthly": "0",
    }


async def test_preview_deal_success_no_auth(client: AsyncClient) -> None:
    """POST /api/v1/deals/preview returns metrics without auth, no save to DB."""
    response = await client.post("/api/v1/deals/preview", json=_preview_payload())
    assert response.status_code == 200
    data = response.json()
    assert "noi" in data
    assert "cap_rate" in data
    assert "monthly_cash_flow" in data
    assert "risk_score" in data
    assert "risk_factors" in data
    assert "id" not in data
    assert "created_at" not in data


async def test_preview_deal_value_error_returns_400(client: AsyncClient) -> None:
    """When DealCalculator raises ValueError, preview returns 400."""
    with patch(
        "app.routers.deals.DealCalculator.calculate_all",
        side_effect=ValueError("purchase_price must be positive"),
    ):
        response = await client.post("/api/v1/deals/preview", json=_preview_payload())
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


async def test_create_deal_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """POST /api/v1/deals with valid property_id and data returns 201."""
    response = await client.post(
        "/api/v1/deals/",
        json=_deal_payload_for_property(str(test_property.id)),
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == str(test_property.id)
    assert data["deal_name"] == "Sheboygan Duplex Deal"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data
    assert data.get("noi") is not None
    assert data.get("cap_rate") is not None


async def test_list_deals_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """GET /api/v1/deals returns 200 and list."""
    response = await client.get("/api/v1/deals/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["id"] == str(test_deal.id) for item in data)


async def test_list_deals_filter_by_property_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
    test_property,
) -> None:
    """GET /api/v1/deals?property_id= returns only deals for that property."""
    response = await client.get(
        "/api/v1/deals/",
        params={"property_id": str(test_property.id)},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(d["property_id"] == str(test_property.id) for d in data)


async def test_get_deal_by_id_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """GET /api/v1/deals/{id} returns 200 and deal."""
    response = await client.get(f"/api/v1/deals/{test_deal.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(test_deal.id)
    assert response.json()["deal_name"] == "Sheboygan Duplex"


async def test_update_deal_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """PUT /api/v1/deals/{id} returns 200 and updated deal."""
    response = await client.put(
        f"/api/v1/deals/{test_deal.id}",
        json={"deal_name": "Updated Deal", "gross_monthly_rent": "2400"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["deal_name"] == "Updated Deal"
    assert response.json()["gross_monthly_rent"] in (2400, 2400.0, "2400", "2400.00")


async def test_delete_deal_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """DELETE /api/v1/deals/{id} returns 204; then GET returns 404."""
    response = await client.delete(
        f"/api/v1/deals/{test_deal.id}", headers=auth_headers
    )
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/deals/{test_deal.id}", headers=auth_headers)
    assert get_resp.status_code == 404


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


async def test_create_deal_invalid_body(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST with missing required fields returns 422."""
    response = await client.post(
        "/api/v1/deals/",
        json={
            "property_id": str(uuid.uuid4()),
            # missing purchase_price, gross_monthly_rent
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_create_deal_property_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST with non-existent property_id returns 404."""
    response = await client.post(
        "/api/v1/deals/",
        json={
            "property_id": str(uuid.uuid4()),
            "purchase_price": "200000",
            "gross_monthly_rent": "2000",
        },
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_create_deal_calculator_value_error_returns_400(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """When DealCalculator.calculate_all raises ValueError, API returns 400 with error_code."""
    with patch(
        "app.routers.deals.DealCalculator.calculate_all",
        side_effect=ValueError("purchase_price must be positive"),
    ):
        response = await client.post(
            "/api/v1/deals/",
            json=_deal_payload_for_property(str(test_property.id)),
            headers=auth_headers,
        )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    # FastAPI nests our dict under "detail", so detail may be {"detail": "...", "error_code": "..."}
    if isinstance(data["detail"], dict):
        assert data["detail"].get("error_code") == "INVALID_DEAL_INPUTS"
        assert "positive" in str(data["detail"].get("detail", ""))
    else:
        assert "positive" in str(data["detail"])


async def test_user_b_cannot_see_user_a_deal(
    client: AsyncClient,
    test_deal,
    create_user,
) -> None:
    """User B cannot access User A's deal (GET/list/PUT/DELETE)."""
    _, _, headers_b = await create_user(full_name="User B")

    get_resp = await client.get(f"/api/v1/deals/{test_deal.id}", headers=headers_b)
    assert get_resp.status_code == 404

    list_resp = await client.get("/api/v1/deals/", headers=headers_b)
    assert list_resp.status_code == 200
    ids = [d["id"] for d in list_resp.json()]
    assert str(test_deal.id) not in ids

    put_resp = await client.put(
        f"/api/v1/deals/{test_deal.id}",
        json={"deal_name": "Hacked"},
        headers=headers_b,
    )
    assert put_resp.status_code == 404

    del_resp = await client.delete(f"/api/v1/deals/{test_deal.id}", headers=headers_b)
    assert del_resp.status_code == 404


async def test_user_b_cannot_create_deal_for_user_a_property(
    client: AsyncClient,
    test_property,
    create_user,
) -> None:
    """User B tries to create a deal for User A's property -> 404."""
    _, _, headers_b = await create_user(full_name="User B")

    response = await client.post(
        "/api/v1/deals/",
        json=_deal_payload_for_property(str(test_property.id)),
        headers=headers_b,
    )
    assert response.status_code == 404
