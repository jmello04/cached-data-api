"""Decorator that wraps FastAPI route handlers with transparent Redis caching."""

import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.cache.client import cache_get, cache_set
from app.core.config import settings


def _build_cache_key(prefix: str, request: Request) -> str:
    """Derive a deterministic Redis key from the request path and query parameters.

    The key is namespaced by ``settings.CACHE_KEY_PREFIX`` and truncated to a
    16-character SHA-256 digest to keep key lengths manageable while avoiding
    collisions across different parameter combinations.

    Args:
        prefix: Logical namespace for the endpoint (e.g. ``"summary"``).
        request: Incoming FastAPI request used to extract path and query params.

    Returns:
        Redis key in the form ``<prefix>:<cache_prefix>:<digest>``.
    """
    params = dict(sorted(request.query_params.items()))
    raw = f"{prefix}:{request.url.path}:{json.dumps(params, sort_keys=True)}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{settings.CACHE_KEY_PREFIX}:{prefix}:{digest}"


def _extract_request(*args: Any, **kwargs: Any) -> Optional[Request]:
    """Extract the FastAPI Request object from arbitrary positional/keyword args.

    FastAPI injects ``Request`` either as a keyword argument or as a positional
    argument depending on how the dependency is declared. This helper searches
    both to ensure the decorator works in either case.

    Args:
        *args: Positional arguments forwarded from the decorated function call.
        **kwargs: Keyword arguments forwarded from the decorated function call.

    Returns:
        The first ``Request`` instance found, or None if none is present.
    """
    if "request" in kwargs:
        return kwargs["request"]
    for arg in args:
        if isinstance(arg, Request):
            return arg
    return None


def cache_response(ttl: int, prefix: Optional[str] = None) -> Callable:
    """Decorator factory that adds transparent response caching to a route handler.

    On a cache **hit** the decorated handler is bypassed entirely and the cached
    JSON payload is returned with an ``X-Cache: HIT`` header.  On a cache
    **miss** the handler executes normally, the result is stored in Redis for
    ``ttl`` seconds, and the response includes ``X-Cache: MISS`` and
    ``X-Cache-TTL`` headers.  Both paths attach an ``X-Response-Time`` header
    measuring the total wall-clock duration of the request.

    Args:
        ttl: Cache expiration in seconds. Controls how long the response is
             served from Redis before the underlying handler is invoked again.
        prefix: Optional Redis key namespace. Defaults to the decorated
                function's ``__name__`` when omitted.

    Returns:
        A decorator that wraps an async route handler with caching logic.

    Example::

        @router.get("/summary")
        @cache_response(ttl=300, prefix="summary")
        async def get_summary(request: Request, db: AsyncSession = Depends(...)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = _extract_request(*args, **kwargs)
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
                        },
                    )

            result = await func(*args, **kwargs)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

            if isinstance(result, dict):
                if cache_key:
                    await cache_set(cache_key, result, ttl)
                return JSONResponse(
                    content=result,
                    headers={
                        "X-Cache": "MISS",
                        "X-Response-Time": f"{elapsed_ms}ms",
                        "X-Cache-TTL": str(ttl),
                    },
                )

            if isinstance(result, Response):
                result.headers["X-Cache"] = "MISS"
                result.headers["X-Response-Time"] = f"{elapsed_ms}ms"
                result.headers["X-Cache-TTL"] = str(ttl)

            return result

        return wrapper

    return decorator
