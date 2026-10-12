"""Unit tests for ResilientCache: degradation, expiry, and recovery to Redis."""

from typing import Dict, Optional

import redis

from src.ingestion.cache import ResilientCache


class _FakeRedis:
    """In-process stand-in for redis.Redis with an on/off switch."""

    def __init__(self) -> None:
        self.store: Dict[str, str] = {}
        self.up = True

    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        if not self.up:
            raise redis.ConnectionError("down")
        self.store[key] = value

    def get(self, key: str) -> Optional[str]:
        if not self.up:
            raise redis.ConnectionError("down")
        return self.store.get(key)


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_values_round_trip_through_redis_when_up() -> None:
    client = _FakeRedis()
    cache = ResilientCache(client, clock=_Clock())

    cache.set("k", {"a": 1})

    assert cache.get("k") == {"a": 1}
    assert not cache.degraded
    assert "k" in client.store


def test_outage_logs_once_and_serves_from_memory(caplog) -> None:
    client = _FakeRedis()
    client.up = False
    cache = ResilientCache(client, clock=_Clock())

    cache.set("k", [1, 2])
    cache.set("j", "x")

    assert cache.get("k") == [1, 2]
    assert cache.degraded
    assert caplog.text.count("falling back to in-memory cache") == 1


def test_memory_entries_expire() -> None:
    client = _FakeRedis()
    client.up = False
    clock = _Clock()
    cache = ResilientCache(client, clock=clock)

    cache.set("k", "v", ttl_s=10)
    clock.now = 10.0

    assert cache.get("k") is None


def test_redis_is_retried_after_window_and_recovers() -> None:
    client = _FakeRedis()
    client.up = False
    clock = _Clock()
    cache = ResilientCache(client, retry_after_s=30.0, clock=clock)
    cache.set("k", "v")
    assert cache.degraded

    client.up = True
    clock.now = 29.0
    cache.set("early", "x")
    assert cache.degraded
    assert "early" not in client.store

    clock.now = 31.0
    cache.set("late", "y")
    assert not cache.degraded
    assert client.store["late"] == '"y"'
