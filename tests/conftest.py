import json
from unittest.mock import AsyncMock

import pytest

from app.cache.client import reset_stats


@pytest.fixture(autouse=True)
def reset_cache_stats_fixture():
    reset_stats()
    yield
    reset_stats()


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.keys = AsyncMock(return_value=[])
    redis.delete = AsyncMock(return_value=0)
    redis.ping = AsyncMock(return_value=True)
    redis.info = AsyncMock(return_value={"used_memory_human": "1.00M"})
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


@pytest.fixture
def sample_category_report():
    return {
        "total_categories": 10,
        "categories": [
            {
                "category": "Tecnologia",
                "total_amount": 3500000.00,
                "transaction_count": 500,
                "average_amount": 7000.00,
                "max_amount": 49998.76,
                "min_amount": 50.00,
                "percentage_of_total": 28.36,
                "top_merchant": "Amazon AWS",
            }
        ],
        "generated_at": "2026-01-01T00:00:00",
    }


@pytest.fixture
def sample_top_transactions():
    return {
        "limit": 10,
        "order_by": "amount",
        "transactions": [
            {
                "id": "abc123",
                "description": "Compra realizada",
                "amount": 49998.76,
                "category": "Investimento",
                "merchant": "XP Investimentos",
                "status": "completed",
                "transaction_date": "2026-01-15 10:30:00",
            }
        ],
        "generated_at": "2026-01-01T00:00:00",
    }
