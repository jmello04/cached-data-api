import json
from unittest.mock import AsyncMock, patch

import pytest

from app.cache.client import cache_get, cache_set, get_cache_stats, reset_stats


class TestCacheGet:
    @pytest.mark.asyncio
    async def test_miss_quando_chave_nao_existe(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            result = await cache_get("test:key:miss")

        assert result is None

    @pytest.mark.asyncio
    async def test_hit_retorna_valor_deserializado(self):
        payload = {"total": 100, "amount": 9999.99}
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(payload)

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            result = await cache_get("test:key:hit")

        assert result == payload

    @pytest.mark.asyncio
    async def test_miss_incrementa_contador(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_get("k:miss")

        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.info = AsyncMock(return_value={"used_memory_human": "1M"})

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert stats["misses"] == 1
        assert stats["hits"] == 0

    @pytest.mark.asyncio
    async def test_hit_incrementa_contador(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({"v": 1})

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_get("k:hit")

        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.info = AsyncMock(return_value={"used_memory_human": "1M"})

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 0


class TestCacheSet:
    @pytest.mark.asyncio
    async def test_serializa_e_persiste_com_ttl(self):
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_set("test:key", {"value": 42}, ttl=60)

        mock_redis.setex.assert_called_once()
        key, ttl, serialized = mock_redis.setex.call_args[0]
        assert key == "test:key"
        assert ttl == 60
        assert json.loads(serialized) == {"value": 42}


class TestCacheStats:
    @pytest.mark.asyncio
    async def test_estrutura_de_retorno(self):
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.info.return_value = {"used_memory_human": "2.50M"}

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert set(stats.keys()) == {"hits", "misses", "hit_rate", "active_keys", "memory_used"}
        assert stats["active_keys"] == 3
        assert stats["memory_used"] == "2.50M"

    @pytest.mark.asyncio
    async def test_calculo_de_hit_rate(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = [
            json.dumps({"x": 1}),
            json.dumps({"x": 2}),
            None,
        ]

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_get("k1")
            await cache_get("k2")
            await cache_get("k3")

        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.info = AsyncMock(return_value={"used_memory_human": "1M"})

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(66.67, abs=0.01)

    @pytest.mark.asyncio
    async def test_hit_rate_zero_sem_requisicoes(self):
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = []
        mock_redis.info.return_value = {"used_memory_human": "1M"}

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_reset_zera_contadores(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({"v": 1})

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            await cache_get("k1")
            await cache_get("k2")

        reset_stats()

        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.info = AsyncMock(return_value={"used_memory_human": "1M"})

        with patch("app.cache.client.get_redis", return_value=mock_redis):
            stats = await get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_stats_retorna_indisponivel_quando_redis_falha(self):
        async def broken_get_redis():
            raise ConnectionError("Redis indisponível")

        with patch("app.cache.client.get_redis", side_effect=broken_get_redis):
            stats = await get_cache_stats()

        assert stats["active_keys"] == -1
        assert stats["memory_used"] == "indisponível"
