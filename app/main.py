import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import cache as cache_routes
from app.api.routes import reports as reports_routes
from app.cache.client import close_redis, get_redis
from app.core.config import settings
from app.infra.database import models  # noqa: F401 — registra os modelos no Base.metadata
from app.infra.database.session import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Manage application startup and shutdown lifecycle.

    On startup: initialise database tables and establish the Redis connection
    pool so both are ready before the first request is processed.
    On shutdown: close the Redis connection pool gracefully.

    Args:
        app: The FastAPI application instance (required by the protocol).
    """
    await create_tables()
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API de relatórios financeiros com cache inteligente via Redis. "
        "Demonstra ganho real de performance com métricas comparativas de latência."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_response_time_header(request: Request, call_next: Any) -> Response:
    """Middleware that appends wall-clock response time to every HTTP response.

    Only sets ``X-Response-Time`` when the decorated endpoint has not already
    set it (e.g. endpoints wrapped with ``@cache_response`` report their own
    more granular measurement).

    Args:
        request: Incoming HTTP request.
        call_next: ASGI callable that processes the request and returns a response.

    Returns:
        The response with the ``X-Response-Time`` header attached.
    """
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
    if "X-Response-Time" not in response.headers:
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
    return response


app.include_router(reports_routes.router)
app.include_router(cache_routes.router)


@app.get("/", tags=["Health"])
async def root() -> dict:
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unavailable"

    return JSONResponse(
        content={
            "status": "healthy",
            "redis": redis_status,
        }
    )
