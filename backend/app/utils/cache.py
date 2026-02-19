from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

import redis
from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None
_redis_unavailable_logged = False


def make_rentcast_cache_key(endpoint: str, address_or_zip: str) -> str:
    """Build a safe, consistent RentCast cache key using a hashed identifier."""
    normalized_value = address_or_zip.strip().lower()
    value_hash = hashlib.sha256(normalized_value.encode("utf-8")).hexdigest()
    return f"rentcast:{endpoint}:{value_hash}"


def _get_redis_client() -> Optional[redis.Redis]:
    """Return a Redis client or None when Redis is unavailable/misconfigured."""
    global _redis_client
    global _redis_unavailable_logged

    if not settings.redis_url:
        if not _redis_unavailable_logged:
            logger.warning(
                "service=redis event=disabled reason=missing_redis_url",
            )
            _redis_unavailable_logged = True
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        _redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        _redis_client.ping()
        return _redis_client
    except Exception as exc:  # pragma: no cover - defensive for env-specific failures
        if not _redis_unavailable_logged:
            logger.warning(
                "service=redis event=unavailable reason=connection_failed error=%s",
                str(exc),
            )
            _redis_unavailable_logged = True
        _redis_client = None
        return None


def get_cached(key: str) -> Optional[Dict[str, Any]]:
    """
    Get cached JSON data by key.

    Returns None when key is absent, Redis is unavailable, or data is invalid.
    """
    client = _get_redis_client()
    if client is None:
        return None

    try:
        raw = client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        return None
    except Exception as exc:  # pragma: no cover - defensive for runtime cache failures
        logger.warning(
            "service=redis event=get_failed key=%s error=%s",
            key,
            str(exc),
        )
        return None


def set_cached(key: str, data: Dict[str, Any], ttl_seconds: int) -> None:
    """
    Cache JSON data with TTL.

    If Redis is unavailable, this operation is skipped and only logged.
    """
    client = _get_redis_client()
    if client is None:
        return

    try:
        payload = json.dumps(data)
        client.setex(key, ttl_seconds, payload)
    except Exception as exc:  # pragma: no cover - defensive for runtime cache failures
        logger.warning(
            "service=redis event=set_failed key=%s ttl_seconds=%s error=%s",
            key,
            ttl_seconds,
            str(exc),
        )
