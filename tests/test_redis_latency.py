"""
Redis latency test (WO8): p99 under 50 ms across 1000 SET/GET operations.

Requires a running Redis (REDIS_URL from .env) and RUN_LOAD_TESTS=1.
"""

import math
import time
import uuid

import pytest

from src.config import config as load_config
from tests.conftest import live_only

P99_BUDGET_MS = 50.0
OPERATIONS = 1000


def _redis_client():
    """Return a connected Redis client, or None if the server is unreachable."""
    import redis

    url = load_config().redis_url
    client = redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=2)
    try:
        client.ping()
    except redis.RedisError:
        return None
    return client


@live_only
def test_redis_p99_latency_under_budget() -> None:
    """p99 of 1000 alternating SET/GET operations stays below 50 ms."""
    client = _redis_client()
    if client is None:
        pytest.skip("Redis not reachable at REDIS_URL (start stack with docker compose up -d)")

    prefix = f"loadtest:{uuid.uuid4().hex}"
    latencies = []
    try:
        for i in range(OPERATIONS):
            key = f"{prefix}:{i}"
            start = time.perf_counter()
            if i % 2 == 0:
                client.set(key, "x", ex=60)
            else:
                client.get(key)
            latencies.append((time.perf_counter() - start) * 1000)
    finally:
        for i in range(0, OPERATIONS, 2):
            client.delete(f"{prefix}:{i}")

    latencies.sort()
    p99 = latencies[math.ceil(0.99 * len(latencies)) - 1]
    assert p99 < P99_BUDGET_MS, f"Redis p99 {p99:.2f} ms exceeds {P99_BUDGET_MS} ms"
