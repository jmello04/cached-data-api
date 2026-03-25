from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.cache.client import cache_delete_pattern, get_cache_stats, reset_stats
from app.core.config import settings

router = APIRouter(prefix="/cache", tags=["Gerenciamento de Cache"])


@router.post(
    "/invalidate",
    summary="Invalida o cache manualmente",
    response_description="Confirmação com total de chaves removidas",
)
async def invalidate_cache(pattern: Optional[str] = None) -> JSONResponse:
    target = (
        f"{settings.CACHE_KEY_PREFIX}:{pattern}:*"
        if pattern
        else f"{settings.CACHE_KEY_PREFIX}:*"
    )

    deleted_count = await cache_delete_pattern(target)
    reset_stats()

    return JSONResponse(
        content={
            "message": "Cache invalidado com sucesso",
            "pattern_used": target,
            "keys_removed": deleted_count,
        }
    )


@router.get(
    "/stats",
    summary="Métricas do cache Redis",
    response_description="Estatísticas de hits, misses, hit_rate, active_keys e memória",
)
async def get_stats() -> JSONResponse:
    stats = await get_cache_stats()
    return JSONResponse(content=stats)
