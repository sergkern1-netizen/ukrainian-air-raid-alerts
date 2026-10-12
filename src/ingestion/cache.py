"""
Redis cache with in-memory fallback (WO8 chaos requirement).

When Redis is unreachable, reads and writes move to a process-local dict and a
single warning is logged. Redis is retried after `retry_after_s` seconds. Values
are JSON-encoded so both paths return the same types.
"""

import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple

import redis

logger = logging.getLogger(__name__)


class ResilientCache:
    """Key-value cache that degrades to memory when Redis fails."""

    def __init__(
        self,
        client: redis.Redis,
        retry_after_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """
        Args:
            client: Redis client used while the server is reachable.
            retry_after_s: Seconds to stay in memory-only mode before retrying Redis.
            clock: Monotonic clock; injectable for tests.
        """
        self._client = client
        self._retry_after_s = retry_after_s
        self._clock = clock
        self._memory: Dict[str, Tuple[float, str]] = {}
        self._retry_at: Optional[float] = None

    @property
    def degraded(self) -> bool:
        """True while Redis is being bypassed."""
        return self._retry_at is not None

    def _redis_usable(self) -> bool:
        """Return True if Redis should be tried now."""
        return self._retry_at is None or self._clock() >= self._retry_at

    def _degrade(self, error: Exception) -> None:
        """Switch to memory-only mode and log the first failure."""
        if self._retry_at is None:
            logger.warning(f"Redis unavailable ({error}); falling back to in-memory cache")
        self._retry_at = self._clock() + self._retry_after_s

    def set(self, key: str, value: Any, ttl_s: float = 300.0) -> None:
        """
        Store a JSON-serializable value with a time-to-live.

        Args:
            key: Cache key.
            value: JSON-serializable value.
            ttl_s: Expiry in seconds.
        """
        payload = json.dumps(value)
        if self._redis_usable():
            try:
                self._client.set(key, payload, ex=int(ttl_s))
                self._retry_at = None
                return
            except redis.RedisError as e:
                self._degrade(e)
        self._memory[key] = (self._clock() + ttl_s, payload)

    def get(self, key: str) -> Any:
        """
        Fetch a value, or None if missing or expired.

        Args:
            key: Cache key.

        Returns:
            Decoded value, or None.
        """
        if self._redis_usable():
            try:
                raw = self._client.get(key)
                self._retry_at = None
                return None if raw is None else json.loads(raw)
            except redis.RedisError as e:
                self._degrade(e)

        entry = self._memory.get(key)
        if entry is None:
            return None
        expires_at, payload = entry
        if self._clock() >= expires_at:
            del self._memory[key]
            return None
        return json.loads(payload)
