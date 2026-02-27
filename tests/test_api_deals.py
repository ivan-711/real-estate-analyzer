"""
Tests for Deal CRUD API endpoints.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
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


# ── Deal Summary endpoint tests ──────────────────────────────────────────


async def test_deals_summary_empty_portfolio(
    client: AsyncClient,
    create_user,
) -> None:
    """User with no deals gets 200 with active_deal_count 0, sums 0, averages null."""
    _, _, headers = await create_user(full_name="Empty Portfolio User")

    response = await client.get("/api/v1/deals/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active_deal_count"] == 0
    assert float(data["total_monthly_cash_flow"]) == 0
    assert float(data["total_equity"]) == 0
    assert data["average_cap_rate"] is None
    assert data["average_cash_on_cash"] is None
    assert data["average_risk_score"] is None


async def test_deals_summary_single_deal(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """Summary for a single deal matches that deal's metrics."""
    create_resp = await client.post(
        "/api/v1/deals/",
        json=_deal_payload_for_property(str(test_property.id)),
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    deal = create_resp.json()

    response = await client.get("/api/v1/deals/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active_deal_count"] == 1

    if deal.get("monthly_cash_flow") is not None:
        assert float(data["total_monthly_cash_flow"]) == float(
            deal["monthly_cash_flow"]
        )
    if deal.get("total_cash_invested") is not None:
        assert float(data["total_equity"]) == float(deal["total_cash_invested"])
    if deal.get("cap_rate") is not None:
        assert float(data["average_cap_rate"]) == float(deal["cap_rate"])
    if deal.get("cash_on_cash") is not None:
        assert float(data["average_cash_on_cash"]) == float(deal["cash_on_cash"])
    if deal.get("risk_score") is not None:
        assert float(data["average_risk_score"]) == float(deal["risk_score"])


async def test_deals_summary_multiple_deals(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_property,
) -> None:
    """Averages and sums are correct across multiple deals."""
    payload_a = _deal_payload_for_property(str(test_property.id))
    payload_a["deal_name"] = "Deal A"
    payload_a["gross_monthly_rent"] = "1800"

    payload_b = _deal_payload_for_property(str(test_property.id))
    payload_b["deal_name"] = "Deal B"
    payload_b["gross_monthly_rent"] = "2200"

    resp_a = await client.post("/api/v1/deals/", json=payload_a, headers=auth_headers)
    assert resp_a.status_code == 201
    deal_a = resp_a.json()

    resp_b = await client.post("/api/v1/deals/", json=payload_b, headers=auth_headers)
    assert resp_b.status_code == 201
    deal_b = resp_b.json()

    response = await client.get("/api/v1/deals/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active_deal_count"] == 2

    if (
        deal_a.get("monthly_cash_flow") is not None
        and deal_b.get("monthly_cash_flow") is not None
    ):
        expected_cf = float(deal_a["monthly_cash_flow"]) + float(
            deal_b["monthly_cash_flow"]
        )
        assert abs(float(data["total_monthly_cash_flow"]) - expected_cf) < 0.02

    if (
        deal_a.get("total_cash_invested") is not None
        and deal_b.get("total_cash_invested") is not None
    ):
        expected_eq = float(deal_a["total_cash_invested"]) + float(
            deal_b["total_cash_invested"]
        )
        assert abs(float(data["total_equity"]) - expected_eq) < 0.02

    if deal_a.get("cap_rate") is not None and deal_b.get("cap_rate") is not None:
        expected_avg_cap = (float(deal_a["cap_rate"]) + float(deal_b["cap_rate"])) / 2
        assert abs(float(data["average_cap_rate"]) - expected_avg_cap) < 0.01

    if (
        deal_a.get("cash_on_cash") is not None
        and deal_b.get("cash_on_cash") is not None
    ):
        expected_avg_coc = (
            float(deal_a["cash_on_cash"]) + float(deal_b["cash_on_cash"])
        ) / 2
        assert abs(float(data["average_cash_on_cash"]) - expected_avg_coc) < 0.01


async def test_deals_summary_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/deals/summary without token returns 401."""
    response = await client.get("/api/v1/deals/summary")
    assert response.status_code == 401


# ── Projections endpoint tests ────────────────────────────────────────────────


async def test_get_projections_default_params(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """GET /projections with defaults returns 10 yearly entries and both IRR values."""
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/projections",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["deal_id"] == str(test_deal.id)
    assert data["deal_name"] == "Sheboygan Duplex"
    assert data["parameters"]["projection_years"] == 10

    projections = data["yearly_projections"]
    assert len(projections) == 10

    # All required fields present and non-null in every year.
    required_fields = [
        "year",
        "property_value",
        "loan_balance",
        "equity",
        "principal_paid",
        "interest_paid",
        "annual_gross_rent",
        "annual_expenses",
        "annual_mortgage_payment",
        "annual_net_cash_flow",
        "cumulative_cash_flow",
    ]
    for row in projections:
        for field in required_fields:
            assert field in row, f"Missing field: {field}"
            assert row[field] is not None, f"Field is None: {field}"

    # Year numbers are sequential 1–10.
    assert [row["year"] for row in projections] == list(range(1, 11))

    # IRR values are present (may be negative for this deal, but not None).
    assert "irr_5_year" in data
    assert "irr_10_year" in data


async def test_get_projections_custom_years(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """GET /projections?years=5 returns exactly 5 yearly entries."""
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/projections?years=5",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["yearly_projections"]) == 5
    assert data["parameters"]["projection_years"] == 5
    # 10-year IRR is None when projection horizon is only 5 years.
    assert data["irr_10_year"] is None


async def test_get_projections_custom_appreciation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """Year 10 property value reflects 5% annual compound appreciation."""
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/projections?years=10&appreciation_pct=5.0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    projections = response.json()["yearly_projections"]

    year10_value = float(projections[9]["property_value"])
    expected = 220_000 * (1.05**10)  # ≈ 358_356.82
    assert abs(year10_value - expected) < 1.00


async def test_get_projections_zero_appreciation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """With 0% appreciation every year's property_value equals the purchase price."""
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/projections?appreciation_pct=0.0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    projections = response.json()["yearly_projections"]

    for row in projections:
        assert abs(float(row["property_value"]) - 220_000) < 0.01


async def test_get_projections_cash_purchase(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session,
    test_property,
    test_user,
) -> None:
    """All-cash deal: loan_balance is 0 every year; equity equals property value."""
    from app.models.deal import Deal

    cash_deal = Deal(
        property_id=test_property.id,
        user_id=test_user.id,
        deal_name="All Cash",
        purchase_price=Decimal("200000"),
        gross_monthly_rent=Decimal("1600"),
        loan_amount=Decimal("0"),
        monthly_mortgage=Decimal("0"),
        total_cash_invested=Decimal("200000"),
        down_payment_pct=Decimal("100"),
    )
    db_session.add(cash_deal)
    await db_session.commit()
    await db_session.refresh(cash_deal)

    response = await client.get(
        f"/api/v1/deals/{cash_deal.id}/projections",
        headers=auth_headers,
    )
    assert response.status_code == 200
    projections = response.json()["yearly_projections"]
    assert len(projections) == 10

    for row in projections:
        assert float(row["loan_balance"]) == 0.0
        assert float(row["interest_paid"]) == 0.0
        assert float(row["principal_paid"]) == 0.0
        # equity = property_value when no debt
        assert abs(float(row["equity"]) - float(row["property_value"])) < 0.01


async def test_get_projections_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /projections for a nonexistent deal returns 404."""
    response = await client.get(
        f"/api/v1/deals/{uuid.uuid4()}/projections",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_get_projections_unauthorized(
    client: AsyncClient,
    test_deal,
    create_user,
) -> None:
    """User B cannot access User A's deal projections (returns 404)."""
    _, _, headers_b = await create_user(full_name="User B")

    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/projections",
        headers=headers_b,
    )
    assert response.status_code == 404


async def test_get_projections_equity_increases(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """Equity at year 10 exceeds equity at year 1 (appreciation + principal paydown)."""
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/projections",
        headers=auth_headers,
    )
    assert response.status_code == 200
    projections = response.json()["yearly_projections"]

    equity_year1 = float(projections[0]["equity"])
    equity_year10 = float(projections[9]["equity"])
    assert equity_year10 > equity_year1


async def test_get_projections_irr_reasonable(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """IRR values, when present, fall within plausible real-estate bounds (-50% to +100%)."""
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/projections",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    if data["irr_5_year"] is not None:
        assert -0.50 < float(data["irr_5_year"]) < 1.00

    if data["irr_10_year"] is not None:
        assert -0.50 < float(data["irr_10_year"]) < 1.00


# ── CSV Export tests ──────────────────────────────────────────────────────────


async def test_export_all_deals_csv_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """GET /export/csv returns 200 with text/csv and header + data row."""
    response = await client.get("/api/v1/deals/export/csv", headers=auth_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    lines = response.text.strip().splitlines()
    assert len(lines) >= 2  # header + at least one row
    assert "Deal Name" in lines[0]
    assert "Purchase Price" in lines[0]


async def test_export_all_deals_csv_empty(
    client: AsyncClient,
    create_user,
) -> None:
    """User with 0 deals gets header-only CSV."""
    _, _, headers = await create_user(full_name="Empty User")
    response = await client.get("/api/v1/deals/export/csv", headers=headers)
    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert len(lines) == 1  # header row only


async def test_export_single_deal_csv_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_deal,
) -> None:
    """GET /{deal_id}/export/csv returns 200 with attachment content-disposition."""
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/export/csv", headers=auth_headers
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".csv" in cd
    lines = response.text.strip().splitlines()
    assert len(lines) == 2  # header + one data row


async def test_export_single_deal_csv_wrong_user(
    client: AsyncClient,
    test_deal,
    create_user,
) -> None:
    """User B cannot export User A's deal — returns 404."""
    _, _, headers_b = await create_user(full_name="User B")
    response = await client.get(
        f"/api/v1/deals/{test_deal.id}/export/csv", headers=headers_b
    )
    assert response.status_code == 404
