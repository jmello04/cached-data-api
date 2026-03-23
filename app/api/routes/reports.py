import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.client import cache_get, cache_set
from app.cache.decorator import cache_response
from app.infra.database.session import get_async_db
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Relatórios Financeiros"])


@router.get(
    "/summary",
    summary="Relatório geral com cache de 5 minutos",
    response_description="Sumário financeiro agregado de todas as transações",
)
@cache_response(ttl=300, prefix="summary")
async def get_summary(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    service = ReportService(db)
    return await service.get_summary_report()


@router.get(
    "/by-category",
    summary="Agrupamento por categoria com cache de 10 minutos",
    response_description="Relatório de transações agrupadas por categoria",
)
@cache_response(ttl=600, prefix="by_category")
async def get_by_category(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    service = ReportService(db)
    return await service.get_by_category_report()


@router.get(
    "/top-transactions",
    summary="Top N transações com cache de 2 minutos",
    response_description="Transações de maior valor",
)
@cache_response(ttl=120, prefix="top_transactions")
async def get_top_transactions(
    request: Request,
    limit: int = Query(default=10, ge=1, le=100, description="Quantidade de registros"),
    order_by: str = Query(default="amount", description="Campo para ordenação: amount | transaction_date"),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    service = ReportService(db)
    return await service.get_top_transactions(limit=limit, order_by=order_by)
