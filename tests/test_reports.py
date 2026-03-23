from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.keys = AsyncMock(return_value=[])
    redis.ping = AsyncMock(return_value=True)
    redis.info = AsyncMock(return_value={"used_memory_human": "1M"})
    return redis


@pytest.fixture
def sample_summary():
    return {
        "total_records": 5000,
        "total_amount": 12345678.90,
        "average_amount": 2469.14,
        "max_amount": 49998.76,
        "min_amount": 8.05,
        "std_deviation": 7231.55,
        "total_categories": 10,
        "total_merchants": 58,
        "status_distribution": {"completed": 4200, "pending": 600, "refunded": 200},
        "monthly_totals": [],
        "generated_at": "2026-01-01T00:00:00",
    }


class TestReportsEndpoints:
    @pytest.mark.asyncio
    async def test_summary_returns_200_on_cache_miss(self, mock_redis, sample_summary):
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
        assert "X-Cache" in response.headers
        assert response.headers["X-Cache"] == "MISS"

    @pytest.mark.asyncio
    async def test_summary_returns_hit_header_when_cached(
        self, mock_redis, sample_summary
    ):
        import json

        mock_redis.get = AsyncMock(return_value=json.dumps(sample_summary))

        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/summary")

        assert response.status_code == 200
        assert response.headers.get("X-Cache") == "HIT"

    @pytest.mark.asyncio
    async def test_response_time_header_present(self, mock_redis, sample_summary):
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
        time_header = response.headers["X-Response-Time"]
        assert time_header.endswith("ms")

    @pytest.mark.asyncio
    async def test_top_transactions_accepts_limit_param(self, mock_redis):
        sample = {
            "limit": 5,
            "order_by": "amount",
            "transactions": [],
            "generated_at": "2026-01-01T00:00:00",
        }

        with (
            patch("app.cache.client._redis_client", mock_redis),
            patch(
                "app.services.report_service.ReportService.get_top_transactions",
                new_callable=AsyncMock,
                return_value=sample,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/reports/top-transactions?limit=5")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint(self, mock_redis):
        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_cache_invalidate_endpoint(self, mock_redis):
        mock_redis.keys = AsyncMock(return_value=["key1", "key2"])
        mock_redis.delete = AsyncMock(return_value=2)

        with patch("app.cache.client._redis_client", mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/cache/invalidate")

        assert response.status_code == 200
        data = response.json()
        assert "keys_removed" in data
        assert data["message"] == "Cache invalidado com sucesso"
