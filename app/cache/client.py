"""Async Redis client with in-process hit/miss statistics tracking."""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

_redis_client: Optional[aioredis.Redis] = None

_stats: dict[str, int] = {
    "hits": 0,
    "misses": 0,
}


def _build_redis_url() -> str:
    """Construct the Redis connection URL from application settings.

    Returns:
        A fully qualified Redis URL including optional password authentication.
    """
    if settings.REDIS_PASSWORD:
        return (
            f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}"
            f":{settings.REDIS_PORT}/{settings.REDIS_DB}"
        )
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


async def get_redis() -> aioredis.Redis:
    """Return the shared Redis client, creating it on first call.

    Uses a module-level singleton so the connection pool is reused across
    requests within the same process lifetime.

    Returns:
        Configured async Redis client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            _build_redis_url(),
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the shared Redis connection and reset the singleton.

    Called during application shutdown to release the connection pool
    gracefully before the process exits.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def cache_get(key: str) -> Optional[Any]:
    """Retrieve a cached value by key and update hit/miss counters.

    Args:
        key: Redis key to look up.

    Returns:
        Deserialised Python object if the key exists, otherwise None.
    """
    client = await get_redis()
    raw = await client.get(key)
    if raw is None:
        _stats["misses"] += 1
        return None
    _stats["hits"] += 1
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """Serialise and store a value in Redis with an expiration.

    Args:
        key: Redis key under which the value will be stored.
        value: Python object to serialise as JSON.
        ttl: Time-to-live in seconds before the key expires.
    """
    client = await get_redis()
    serialized = json.dumps(value, default=str)
    await client.setex(key, ttl, serialized)


async def cache_delete_pattern(pattern: str) -> int:
    """Delete all Redis keys matching a glob pattern.

    Args:
        pattern: Redis key pattern (e.g. ``"cached_data_api:reports:*"``).

    Returns:
        Number of keys removed. Returns 0 if no keys matched.
    """
    client = await get_redis()
    keys = await client.keys(pattern)
    if not keys:
        return 0
    return await client.delete(*keys)


async def get_cache_stats() -> dict[str, Any]:
    """Return current cache performance metrics.

    Combines the in-process hit/miss counters with live Redis server data
    (active key count and memory usage). If Redis is unreachable, those
    fields are set to sentinel values rather than raising an exception.

    Returns:
        Dictionary with keys: hits, misses, hit_rate, active_keys, memory_used.
    """
    total = _stats["hits"] + _stats["misses"]
    hit_rate = round(_stats["hits"] / total * 100, 2) if total > 0 else 0.0

    try:
        client = await get_redis()
        prefix_pattern = f"{settings.CACHE_KEY_PREFIX}:*"
        active_keys = len(await client.keys(prefix_pattern))
        info = await client.info("memory")
        memory_used = info.get("used_memory_human", "N/A")
    except Exception:
        active_keys = -1
        memory_used = "indisponível"

    return {
        "hits": _stats["hits"],
        "misses": _stats["misses"],
        "hit_rate": hit_rate,
        "active_keys": active_keys,
        "memory_used": memory_used,
    }


def reset_stats() -> None:
    """Reset in-process hit and miss counters to zero.

    Used in tests to ensure a clean statistics baseline before each test case.
    """
    _stats["hits"] = 0
    _stats["misses"] = 0
