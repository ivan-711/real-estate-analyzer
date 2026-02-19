from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from app.config import settings
from app.utils.cache import get_cached, make_rentcast_cache_key, set_cached

logger = logging.getLogger(__name__)


class RentCastError(Exception):
    """Base exception for RentCast integration errors."""

    status_code: int = 502
    error_code: str = "RENTCAST_ERROR"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class MissingRentCastAPIKey(RentCastError):
    """Raised when RentCast API key is not configured and cache miss occurs."""

    status_code = 503
    error_code = "RENTCAST_API_KEY_MISSING"


class RentCastQuotaExhausted(RentCastError):
    """Raised when RentCast returns HTTP 429 and no cache fallback exists."""

    status_code = 429
    error_code = "RENTCAST_QUOTA_EXHAUSTED"


class PropertyNotFound(RentCastError):
    """Raised when RentCast cannot find the requested property/address."""

    status_code = 404
    error_code = "PROPERTY_NOT_FOUND"


class RentCastServerError(RentCastError):
    """Raised when RentCast has repeated server-side failures."""

    status_code = 502
    error_code = "RENTCAST_SERVER_ERROR"


class ExternalAPIUnavailable(RentCastError):
    """Raised when network failures prevent communication with external API."""

    status_code = 503
    error_code = "EXTERNAL_API_UNAVAILABLE"


SAMPLE_LOOKUP_RESPONSE: Dict[str, Any] = {
    "address": "1515 N 7th St",
    "city": "Sheboygan",
    "state": "WI",
    "zip_code": "53081",
    "county": "Sheboygan",
    "property_type": "duplex",
    "num_units": 2,
    "bedrooms": 5,
    "bathrooms": 2.0,
    "square_footage": 2330,
    "lot_size": 4356,
    "year_built": 1900,
    "rentcast_id": "sample-rentcast-id-1515-n-7th",
    "estimated_value": 220000,
    "rent_estimate_monthly": 1800,
    "rent_estimate_low": 1650,
    "rent_estimate_high": 1950,
    "rent_estimate_confidence": 0.84,
}


class RentCastClient:
    """Async RentCast API client with cache-first behavior and normalized outputs."""

    BASE_URL = "https://api.rentcast.io/v1"
    TTL_SECONDS = {
        "property": 30 * 24 * 60 * 60,
        "rent": 14 * 24 * 60 * 60,
        "value": 14 * 24 * 60 * 60,
        "market": 30 * 24 * 60 * 60,
        "comps": 48 * 60 * 60,
    }

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        self._api_key = (settings.rentcast_api_key or "").strip()
        self._owns_client = http_client is None

        if http_client is not None:
            self._client = http_client
            if self._api_key and "X-Api-Key" not in self._client.headers:
                self._client.headers["X-Api-Key"] = self._api_key
        else:
            timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0)
            headers = {"X-Api-Key": self._api_key} if self._api_key else {}
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=timeout,
                headers=headers,
            )

    async def __aenter__(self) -> "RentCastClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close owned HTTP client resources."""
        if self._owns_client:
            await self._client.aclose()

    async def lookup_property(self, address: str) -> Dict[str, Any]:
        """Lookup a property by address and return normalized internal property fields."""
        cache_key = make_rentcast_cache_key("property", address)
        cached = get_cached(cache_key)
        if cached is not None:
            self._log_call(
                endpoint="/properties",
                response_time_ms=0,
                cache_hit=True,
                status_code=200,
            )
            return cached

        payload = await self._request_json(
            endpoint="/properties",
            params={"address": address, "limit": 1},
            cache_key=cache_key,
            cache_ttl_seconds=self.TTL_SECONDS["property"],
        )
        normalized = self._normalize_property(payload, fallback_address=address)
        set_cached(cache_key, normalized, self.TTL_SECONDS["property"])
        return normalized

    async def get_rent_estimate(self, address: str) -> Dict[str, Any]:
        """Get long-term rent estimate by address and return normalized internal fields."""
        cache_key = make_rentcast_cache_key("rent", address)
        cached = get_cached(cache_key)
        if cached is not None:
            self._log_call(
                endpoint="/avm/rent/long-term",
                response_time_ms=0,
                cache_hit=True,
                status_code=200,
            )
            return cached

        payload = await self._request_json(
            endpoint="/avm/rent/long-term",
            params={"address": address},
            cache_key=cache_key,
            cache_ttl_seconds=self.TTL_SECONDS["rent"],
        )
        normalized = self._normalize_rent_estimate(payload)
        set_cached(cache_key, normalized, self.TTL_SECONDS["rent"])
        return normalized

    async def get_value_estimate(self, address: str) -> Dict[str, Any]:
        """Get value estimate by address and return normalized internal fields."""
        cache_key = make_rentcast_cache_key("value", address)
        cached = get_cached(cache_key)
        if cached is not None:
            self._log_call(
                endpoint="/avm/value",
                response_time_ms=0,
                cache_hit=True,
                status_code=200,
            )
            return cached

        payload = await self._request_json(
            endpoint="/avm/value",
            params={"address": address},
            cache_key=cache_key,
            cache_ttl_seconds=self.TTL_SECONDS["value"],
        )
        normalized = self._normalize_value_estimate(payload)
        set_cached(cache_key, normalized, self.TTL_SECONDS["value"])
        return normalized

    async def get_rental_comps(
        self,
        address: str,
        radius: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Get rental comps around an address and return normalized comp records."""
        cache_key = make_rentcast_cache_key("comps", f"{address}:{radius}")
        cached = get_cached(cache_key)
        if cached is not None and isinstance(cached.get("items"), list):
            self._log_call(
                endpoint="/listings/rental/long-term",
                response_time_ms=0,
                cache_hit=True,
                status_code=200,
            )
            return cached["items"]

        payload = await self._request_json(
            endpoint="/listings/rental/long-term",
            params={"address": address, "radius": radius},
            cache_key=cache_key,
            cache_ttl_seconds=self.TTL_SECONDS["comps"],
        )
        normalized_items = self._normalize_rental_comps(payload)
        set_cached(cache_key, {"items": normalized_items}, self.TTL_SECONDS["comps"])
        return normalized_items

    async def get_market_stats(self, zip_code: str) -> Dict[str, Any]:
        """Get market-level stats by zip code and return normalized internal fields."""
        cache_key = make_rentcast_cache_key("market", zip_code)
        cached = get_cached(cache_key)
        if cached is not None:
            self._log_call(
                endpoint="/markets",
                response_time_ms=0,
                cache_hit=True,
                status_code=200,
            )
            return cached

        payload = await self._request_json(
            endpoint="/markets",
            params={"zipCode": zip_code},
            cache_key=cache_key,
            cache_ttl_seconds=self.TTL_SECONDS["market"],
        )
        normalized = self._normalize_market_stats(payload, fallback_zip=zip_code)
        set_cached(cache_key, normalized, self.TTL_SECONDS["market"])
        return normalized

    async def _request_json(
        self,
        endpoint: str,
        params: Dict[str, Any],
        cache_key: str,
        cache_ttl_seconds: int,
    ) -> Dict[str, Any]:
        """Perform a GET request with standardized retries, errors, and logging."""
        if not self._api_key:
            raise MissingRentCastAPIKey(
                "RentCast API key is not configured. Set RENTCAST_API_KEY to enable lookups."
            )

        start = time.perf_counter()
        for attempt in range(2):
            try:
                response = await self._client.get(endpoint, params=params)
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
                self._log_call(
                    endpoint=endpoint,
                    response_time_ms=self._elapsed_ms(start),
                    cache_hit=False,
                    status_code=None,
                )
                raise ExternalAPIUnavailable(
                    f"Unable to reach RentCast ({exc.__class__.__name__})."
                ) from exc
            except httpx.RequestError as exc:
                self._log_call(
                    endpoint=endpoint,
                    response_time_ms=self._elapsed_ms(start),
                    cache_hit=False,
                    status_code=None,
                )
                raise ExternalAPIUnavailable(
                    f"Unexpected RentCast request failure ({exc.__class__.__name__})."
                ) from exc

            status_code = response.status_code
            elapsed_ms = self._elapsed_ms(start)

            if status_code == 429:
                remaining = (
                    response.headers.get("x-ratelimit-remaining")
                    or response.headers.get("ratelimit-remaining")
                    or response.headers.get("x-ratelimit-remaining-monthly")
                )
                logger.warning(
                    "service=rentcast endpoint=%s response_time_ms=%s cache_hit=%s "
                    "status_code=%s remaining_quota=%s",
                    endpoint,
                    elapsed_ms,
                    False,
                    status_code,
                    remaining,
                )
                cached = get_cached(cache_key)
                if cached is not None:
                    self._log_call(
                        endpoint=endpoint,
                        response_time_ms=elapsed_ms,
                        cache_hit=True,
                        status_code=status_code,
                    )
                    return cached
                raise RentCastQuotaExhausted(
                    "RentCast monthly quota appears exhausted. Please try again later."
                )

            if status_code == 404:
                self._log_call(
                    endpoint=endpoint,
                    response_time_ms=elapsed_ms,
                    cache_hit=False,
                    status_code=status_code,
                )
                raise PropertyNotFound(
                    "Property not found. Please verify the address format and try again."
                )

            if 500 <= status_code < 600:
                if attempt == 0:
                    logger.warning(
                        "service=rentcast endpoint=%s response_time_ms=%s cache_hit=%s "
                        "status_code=%s event=retry_once_after_2s",
                        endpoint,
                        elapsed_ms,
                        False,
                        status_code,
                    )
                    await asyncio.sleep(2)
                    continue

                cached = get_cached(cache_key)
                if cached is not None:
                    self._log_call(
                        endpoint=endpoint,
                        response_time_ms=elapsed_ms,
                        cache_hit=True,
                        status_code=status_code,
                    )
                    return cached

                self._log_call(
                    endpoint=endpoint,
                    response_time_ms=elapsed_ms,
                    cache_hit=False,
                    status_code=status_code,
                )
                raise RentCastServerError(
                    "RentCast is temporarily unavailable. Please try again shortly."
                )

            if status_code >= 400:
                self._log_call(
                    endpoint=endpoint,
                    response_time_ms=elapsed_ms,
                    cache_hit=False,
                    status_code=status_code,
                )
                raise RentCastServerError(
                    f"RentCast request failed with status code {status_code}."
                )

            self._log_call(
                endpoint=endpoint,
                response_time_ms=elapsed_ms,
                cache_hit=False,
                status_code=status_code,
            )
            try:
                data = response.json()
            except ValueError as exc:
                raise RentCastServerError(
                    "RentCast returned an invalid response payload."
                ) from exc

            # Best-effort warm cache with raw payload to enable fallback on retries.
            if isinstance(data, dict):
                set_cached(cache_key, data, cache_ttl_seconds)
                return data
            if isinstance(data, list):
                wrapped = {"items": data}
                set_cached(cache_key, wrapped, cache_ttl_seconds)
                return wrapped

            raise RentCastServerError(
                "RentCast response payload has unsupported format."
            )

        raise RentCastServerError("RentCast request failed after retry.")

    @staticmethod
    def _extract_record(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the primary object from common RentCast payload shapes."""
        if "items" in payload and isinstance(payload["items"], list):
            return payload["items"][0] if payload["items"] else {}

        if "data" in payload:
            data = payload["data"]
            if isinstance(data, list):
                return data[0] if data else {}
            if isinstance(data, dict):
                return data

        if "property" in payload and isinstance(payload["property"], dict):
            return payload["property"]

        return payload

    def _normalize_property(
        self,
        payload: Dict[str, Any],
        fallback_address: str,
    ) -> Dict[str, Any]:
        """Normalize RentCast property lookup response to internal schema."""
        record = self._extract_record(payload)
        return {
            "address": record.get("addressLine1")
            or record.get("formattedAddress")
            or record.get("address")
            or fallback_address,
            "city": record.get("city"),
            "state": record.get("state"),
            "zip_code": record.get("zipCode") or record.get("zip_code"),
            "county": record.get("county"),
            "property_type": record.get("propertyType")
            or record.get("property_type")
            or record.get("type"),
            "num_units": record.get("numUnits")
            or record.get("units")
            or record.get("num_units"),
            "bedrooms": record.get("bedrooms"),
            "bathrooms": record.get("bathrooms"),
            "square_footage": record.get("squareFootage")
            or record.get("square_footage")
            or record.get("squareFeet"),
            "lot_size": record.get("lotSize")
            or record.get("lot_size")
            or record.get("lotSizeSquareFeet"),
            "year_built": record.get("yearBuilt") or record.get("year_built"),
            "rentcast_id": record.get("id")
            or record.get("propertyId")
            or record.get("rentcast_id"),
        }

    def _normalize_rent_estimate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize rent AVM response for internal rent fields."""
        record = self._extract_record(payload)
        return {
            "rent_estimate_monthly": record.get("rent")
            or record.get("rentEstimate")
            or record.get("estimatedRent")
            or record.get("price")
            or record.get("rent_estimate_monthly"),
            "rent_estimate_low": record.get("rentRangeLow")
            or record.get("rentLow")
            or record.get("low")
            or record.get("rent_estimate_low"),
            "rent_estimate_high": record.get("rentRangeHigh")
            or record.get("rentHigh")
            or record.get("high")
            or record.get("rent_estimate_high"),
            "rent_estimate_confidence": record.get("confidence")
            or record.get("confidenceScore")
            or record.get("rent_estimate_confidence"),
        }

    def _normalize_value_estimate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize value AVM response for internal value fields."""
        record = self._extract_record(payload)
        return {
            "estimated_value": record.get("value")
            or record.get("price")
            or record.get("estimate")
            or record.get("estimated_value"),
            "estimated_value_low": record.get("valueRangeLow")
            or record.get("low")
            or record.get("estimated_value_low"),
            "estimated_value_high": record.get("valueRangeHigh")
            or record.get("high")
            or record.get("estimated_value_high"),
            "value_estimate_confidence": record.get("confidence")
            or record.get("confidenceScore")
            or record.get("value_estimate_confidence"),
        }

    def _normalize_rental_comps(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize rental comp listings into internal comp records."""
        records: List[Dict[str, Any]] = []
        if "items" in payload and isinstance(payload["items"], list):
            records = payload["items"]
        elif "data" in payload and isinstance(payload["data"], list):
            records = payload["data"]
        elif isinstance(payload, dict):
            records = [payload]

        normalized_items: List[Dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            normalized_items.append(
                {
                    "address": record.get("addressLine1")
                    or record.get("formattedAddress")
                    or record.get("address"),
                    "city": record.get("city"),
                    "state": record.get("state"),
                    "zip_code": record.get("zipCode") or record.get("zip_code"),
                    "property_type": record.get("propertyType")
                    or record.get("property_type"),
                    "bedrooms": record.get("bedrooms"),
                    "bathrooms": record.get("bathrooms"),
                    "square_footage": record.get("squareFootage")
                    or record.get("square_footage"),
                    "rent": record.get("rent") or record.get("price"),
                    "distance_miles": record.get("distance")
                    or record.get("distanceMiles"),
                }
            )

        return normalized_items

    def _normalize_market_stats(
        self,
        payload: Dict[str, Any],
        fallback_zip: str,
    ) -> Dict[str, Any]:
        """Normalize market stats response into internal market snapshot fields."""
        record = self._extract_record(payload)
        return {
            "zip_code": record.get("zipCode") or record.get("zip_code") or fallback_zip,
            "city": record.get("city"),
            "state": record.get("state"),
            "median_home_value": record.get("medianHomeValue")
            or record.get("median_home_value"),
            "median_rent": record.get("medianRent") or record.get("median_rent"),
            "avg_vacancy_rate": record.get("vacancyRate")
            or record.get("avg_vacancy_rate"),
            "yoy_appreciation_pct": record.get("yoyAppreciationPct")
            or record.get("yoy_appreciation_pct"),
            "population_growth_pct": record.get("populationGrowthPct")
            or record.get("population_growth_pct"),
            "rent_to_price_ratio": record.get("rentToPriceRatio")
            or record.get("rent_to_price_ratio"),
        }

    @staticmethod
    def _elapsed_ms(start_time: float) -> int:
        return int((time.perf_counter() - start_time) * 1000)

    @staticmethod
    def _log_call(
        endpoint: str,
        response_time_ms: int,
        cache_hit: bool,
        status_code: Optional[int],
    ) -> None:
        """Emit structured-style log fields for every RentCast interaction."""
        logger.info(
            "service=rentcast endpoint=%s response_time_ms=%s cache_hit=%s status_code=%s",
            endpoint,
            response_time_ms,
            cache_hit,
            status_code,
        )
