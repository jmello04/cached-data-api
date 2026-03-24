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
    if settings.REDIS_PASSWORD:
        return (
            f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}"
            f":{settings.REDIS_PORT}/{settings.REDIS_DB}"
        )
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


async def get_redis() -> aioredis.Redis:
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
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def cache_get(key: str) -> Optional[Any]:
    client = await get_redis()
    raw = await client.get(key)
    if raw is None:
        _stats["misses"] += 1
        return None
    _stats["hits"] += 1
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int) -> None:
    client = await get_redis()
    serialized = json.dumps(value, default=str)
    await client.setex(key, ttl, serialized)


async def cache_delete_pattern(pattern: str) -> int:
    client = await get_redis()
    keys = await client.keys(pattern)
    if not keys:
        return 0
    return await client.delete(*keys)


async def get_cache_stats() -> dict:
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
    _stats["hits"] = 0
    _stats["misses"] = 0
