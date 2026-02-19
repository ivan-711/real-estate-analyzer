from __future__ import annotations

import uuid
from typing import Any, Dict

import httpx
import pytest
from app.integrations import rentcast as rentcast_module
from app.integrations.rentcast import (
    ExternalAPIUnavailable,
    MissingRentCastAPIKey,
    PropertyNotFound,
    RentCastClient,
    RentCastQuotaExhausted,
    RentCastServerError,
)
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
            "full_name": "RentCast Test User",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_rentcast_success_lookup_and_rent_estimate(
    monkeypatch,
    sample_rentcast_property_response: Dict[str, object],
) -> None:
    """Client normalizes successful property lookup and rent estimate responses."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "test-key")
    monkeypatch.setattr(rentcast_module, "get_cached", lambda key: None)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/properties"):
            return httpx.Response(
                status_code=200,
                json=[
                    {
                        "addressLine1": "1515 N 7th St",
                        "city": "Sheboygan",
                        "state": "WI",
                        "zipCode": "53081",
                        "county": "Sheboygan",
                        "propertyType": "duplex",
                        "numUnits": 2,
                        "bedrooms": 5,
                        "bathrooms": 2.0,
                        "squareFootage": 2330,
                        "yearBuilt": 1900,
                        "id": "prop-123",
                    }
                ],
            )
        if request.url.path.endswith("/avm/rent/long-term"):
            return httpx.Response(
                status_code=200,
                json={
                    "rent": 1800,
                    "rentRangeLow": 1650,
                    "rentRangeHigh": 1950,
                    "confidence": 0.84,
                },
            )
        return httpx.Response(status_code=500, json={"detail": "unexpected endpoint"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        property_data = await client.lookup_property(
            "1515 N 7th St, Sheboygan, WI 53081"
        )
        rent_data = await client.get_rent_estimate("1515 N 7th St, Sheboygan, WI 53081")

    assert property_data["address"] == sample_rentcast_property_response["address"]
    assert property_data["city"] == sample_rentcast_property_response["city"]
    assert property_data["state"] == sample_rentcast_property_response["state"]
    assert property_data["zip_code"] == sample_rentcast_property_response["zip_code"]
    assert property_data["property_type"] == "duplex"
    assert property_data["square_footage"] == 2330
    assert rent_data["rent_estimate_monthly"] == 1800
    assert rent_data["rent_estimate_low"] == 1650
    assert rent_data["rent_estimate_high"] == 1950


async def test_rentcast_cache_hit_skips_outbound(monkeypatch) -> None:
    """Cache hit should return cached property and not issue outbound HTTP request."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "test-key")

    cached = {
        "address": "cached-address",
        "city": "Sheboygan",
        "state": "WI",
    }
    monkeypatch.setattr(rentcast_module, "get_cached", lambda key: cached)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(status_code=500, json={"detail": "should not be called"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        result = await client.lookup_property("any address")

    assert result == cached
    assert called["count"] == 0


async def test_rentcast_429_with_cache_fallback(monkeypatch) -> None:
    """429 should return cached fallback when cached value exists at error time."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "test-key")

    cache_calls = {"count": 0}

    def fake_get_cached(key: str) -> dict | None:
        cache_calls["count"] += 1
        if cache_calls["count"] == 1:
            return None
        return {"address": "fallback from cache", "city": "Sheboygan"}

    monkeypatch.setattr(rentcast_module, "get_cached", fake_get_cached)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=429,
            headers={"x-ratelimit-remaining": "0"},
            json={"detail": "quota exhausted"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        result = await client.lookup_property("1515 N 7th St, Sheboygan, WI 53081")

    assert result["address"] == "fallback from cache"
    assert cache_calls["count"] >= 2


async def test_rentcast_429_without_cache_raises_quota(monkeypatch) -> None:
    """429 should raise RentCastQuotaExhausted when no cache fallback exists."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "test-key")
    monkeypatch.setattr(rentcast_module, "get_cached", lambda key: None)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=429, json={"detail": "quota exhausted"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        with pytest.raises(RentCastQuotaExhausted):
            await client.lookup_property("1515 N 7th St, Sheboygan, WI 53081")


async def test_rentcast_404_raises_property_not_found(monkeypatch) -> None:
    """404 should raise PropertyNotFound with a helpful message."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "test-key")
    monkeypatch.setattr(rentcast_module, "get_cached", lambda key: None)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        with pytest.raises(PropertyNotFound):
            await client.lookup_property("missing address")


async def test_rentcast_5xx_retries_once_then_raises(monkeypatch) -> None:
    """5xx should retry exactly once, then raise RentCastServerError on second failure."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "test-key")
    monkeypatch.setattr(rentcast_module, "get_cached", lambda key: None)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(rentcast_module.asyncio, "sleep", fake_sleep)

    call_count = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["count"] += 1
        return httpx.Response(status_code=503, json={"detail": "service unavailable"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        with pytest.raises(RentCastServerError):
            await client.lookup_property("1515 N 7th St, Sheboygan, WI 53081")

    assert call_count["count"] == 2


async def test_rentcast_network_error_raises_external_api_unavailable(
    monkeypatch,
) -> None:
    """Network errors should raise ExternalAPIUnavailable."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "test-key")
    monkeypatch.setattr(rentcast_module, "get_cached", lambda key: None)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("dns failure", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        with pytest.raises(ExternalAPIUnavailable):
            await client.lookup_property("1515 N 7th St, Sheboygan, WI 53081")


async def test_rentcast_missing_api_key_raises_clear_error(monkeypatch) -> None:
    """Missing API key should fail fast on cache miss without making external calls."""
    monkeypatch.setattr(rentcast_module.settings, "rentcast_api_key", "")
    monkeypatch.setattr(rentcast_module, "get_cached", lambda key: None)
    monkeypatch.setattr(rentcast_module, "set_cached", lambda key, data, ttl: None)

    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(status_code=200, json={})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url=RentCastClient.BASE_URL,
        transport=transport,
    ) as http_client:
        client = RentCastClient(http_client=http_client)
        with pytest.raises(MissingRentCastAPIKey):
            await client.lookup_property("1515 N 7th St, Sheboygan, WI 53081")

    assert called["count"] == 0


@pytest.mark.parametrize(
    "raised_exception,status_code,error_code",
    [
        (
            RentCastQuotaExhausted("quota exhausted"),
            429,
            "RENTCAST_QUOTA_EXHAUSTED",
        ),
        (
            PropertyNotFound("not found"),
            404,
            "PROPERTY_NOT_FOUND",
        ),
        (
            RentCastServerError("server down"),
            502,
            "RENTCAST_SERVER_ERROR",
        ),
        (
            ExternalAPIUnavailable("network unavailable"),
            503,
            "EXTERNAL_API_UNAVAILABLE",
        ),
        (
            MissingRentCastAPIKey("missing key"),
            503,
            "RENTCAST_API_KEY_MISSING",
        ),
    ],
)
async def test_lookup_endpoint_uses_standard_error_shape(
    client: AsyncClient,
    monkeypatch,
    raised_exception: Exception,
    status_code: int,
    error_code: str,
) -> None:
    """Router + exception handler should return {detail, error_code} for RentCast errors."""
    from app.integrations.rentcast import RentCastClient

    async def fake_lookup(self, address: str) -> Dict[str, Any]:
        raise raised_exception

    monkeypatch.setattr(RentCastClient, "lookup_property", fake_lookup)

    headers = await _auth_headers(client)
    response = await client.post(
        "/api/v1/properties/lookup",
        json={"address": "1515 N 7th St, Sheboygan, WI 53081"},
        headers=headers,
    )

    assert response.status_code == status_code
    payload = response.json()
    assert payload["error_code"] == error_code
    assert "detail" in payload
