import time
from contextlib import asynccontextmanager

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
async def lifespan(app: FastAPI):
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
async def add_response_time_header(request: Request, call_next):
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
