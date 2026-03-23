import hashlib
import json
import time
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.cache.client import cache_get, cache_set
from app.core.config import settings


def _build_cache_key(prefix: str, request: Request) -> str:
    params = dict(sorted(request.query_params.items()))
    raw = f"{prefix}:{request.url.path}:{json.dumps(params, sort_keys=True)}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{settings.CACHE_KEY_PREFIX}:{prefix}:{digest}"


def cache_response(ttl: int, prefix: Optional[str] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            cache_prefix = prefix or func.__name__
            cache_key = _build_cache_key(cache_prefix, request) if request else None

            start_time = time.perf_counter()

            if cache_key:
                cached_value = await cache_get(cache_key)
                if cached_value is not None:
                    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
                    return JSONResponse(
                        content=cached_value,
                        headers={
                            "X-Cache": "HIT",
                            "X-Response-Time": f"{elapsed_ms}ms",
                            "X-Cache-Key": cache_key,
                        },
                    )

            result = await func(*args, **kwargs)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

            if cache_key:
                payload = result if isinstance(result, dict) else result
                if isinstance(result, dict):
                    await cache_set(cache_key, result, ttl)
                    return JSONResponse(
                        content=result,
                        headers={
                            "X-Cache": "MISS",
                            "X-Response-Time": f"{elapsed_ms}ms",
                            "X-Cache-TTL": str(ttl),
                        },
                    )

            if isinstance(result, JSONResponse):
                result.headers["X-Cache"] = "MISS"
                result.headers["X-Response-Time"] = f"{elapsed_ms}ms"
                result.headers["X-Cache-TTL"] = str(ttl)

            return result

        return wrapper

    return decorator
