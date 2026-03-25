import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestSummaryEndpoint:
    @pytest.mark.asyncio
    async def test_retorna_200_no_cache_miss(self, mock_redis, sample_summary):
        with (
            patch("app.cache.client._redis_client", mock_redis),
            patch(
                "app.services.report_service.ReportService.get_summary_report",
                new_callable=AsyncMock,
                return_value=sample_summary,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 5000
        assert data["total_amount"] == 12345678.90

    @pytest.mark.asyncio
    async def test_header_x_cache_miss_na_primeira_requisicao(self, mock_redis, sample_summary):
        with (
            patch("app.cache.client._redis_client", mock_redis),
            patch(
                "app.services.report_service.ReportService.get_summary_report",
                new_callable=AsyncMock,
                return_value=sample_summary,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/summary")

        assert response.headers.get("X-Cache") == "MISS"

    @pytest.mark.asyncio
    async def test_header_x_cache_hit_quando_em_cache(self, mock_redis, sample_summary):
        mock_redis.get = AsyncMock(return_value=json.dumps(sample_summary))

        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/summary")

        assert response.status_code == 200
        assert response.headers.get("X-Cache") == "HIT"

    @pytest.mark.asyncio
    async def test_header_x_response_time_presente(self, mock_redis, sample_summary):
        with (
            patch("app.cache.client._redis_client", mock_redis),
            patch(
                "app.services.report_service.ReportService.get_summary_report",
                new_callable=AsyncMock,
                return_value=sample_summary,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/summary")

        assert "X-Response-Time" in response.headers
        assert response.headers["X-Response-Time"].endswith("ms")


class TestTopTransactionsEndpoint:
    @pytest.mark.asyncio
    async def test_aceita_parametro_limit(self, mock_redis, sample_top_transactions):
        with (
            patch("app.cache.client._redis_client", mock_redis),
            patch(
                "app.services.report_service.ReportService.get_top_transactions",
                new_callable=AsyncMock,
                return_value=sample_top_transactions,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/top-transactions?limit=5")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rejeita_limit_invalido(self, mock_redis):
        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/top-transactions?limit=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejeita_limit_acima_do_maximo(self, mock_redis):
        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/top-transactions?limit=101")

        assert response.status_code == 422


class TestCacheManagementEndpoints:
    @pytest.mark.asyncio
    async def test_invalidate_retorna_confirmacao(self, mock_redis):
        mock_redis.keys = AsyncMock(return_value=["key1", "key2"])
        mock_redis.delete = AsyncMock(return_value=2)

        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/cache/invalidate")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache invalidado com sucesso"
        assert "keys_removed" in data
        assert "pattern_used" in data

    @pytest.mark.asyncio
    async def test_stats_retorna_estrutura_correta(self, mock_redis):
        mock_redis.keys = AsyncMock(return_value=["k1"])
        mock_redis.info = AsyncMock(return_value={"used_memory_human": "512K"})

        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/cache/stats")

        assert response.status_code == 200
        data = response.json()
        assert "hits" in data
        assert "misses" in data
        assert "hit_rate" in data
        assert "active_keys" in data
        assert "memory_used" in data


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health_retorna_status_healthy(self, mock_redis):
        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_retorna_informacoes_da_api(self, mock_redis):
        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "version" in data
        assert "docs" in data
