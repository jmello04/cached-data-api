import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.cache.client import cache_get, cache_set, get_cache_stats, reset_stats


@pytest.fixture(autouse=True)
def reset_cache_stats():
    reset_stats()
    yield
    reset_stats()


class TestCacheClient:
    @pytest.mark.asyncio
    async def test_cache_miss_increments_counter(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            result = await cache_get("test:key:miss")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_returns_value(self):
        payload = {"total": 100, "amount": 9999.99}
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(payload)

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            result = await cache_get("test:key:hit")

        assert result == payload

    @pytest.mark.asyncio
    async def test_cache_set_serializes_correctly(self):
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_set("test:key", {"value": 42}, ttl=60)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        key, ttl, serialized = call_args[0]
        assert key == "test:key"
        assert ttl == 60
        assert json.loads(serialized) == {"value": 42}

    @pytest.mark.asyncio
    async def test_cache_stats_returns_correct_structure(self):
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.info.return_value = {"used_memory_human": "2.50M"}

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "active_keys" in stats
        assert "memory_used" in stats
        assert stats["active_keys"] == 3
        assert stats["memory_used"] == "2.50M"

    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self):
        payload = json.dumps({"x": 1})
        mock_redis = AsyncMock()

        mock_redis.get.side_effect = [payload, payload, None]

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_get("k1")
            await cache_get("k2")
            await cache_get("k3")

        mock_redis.keys.return_value = []
        mock_redis.info.return_value = {"used_memory_human": "1M"}

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(66.67, 0.01)

    @pytest.mark.asyncio
    async def test_reset_stats_zeroes_counters(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({"v": 1})

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_get("k1")
            await cache_get("k2")

        reset_stats()

        mock_redis.keys.return_value = []
        mock_redis.info.return_value = {"used_memory_human": "1M"}

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
