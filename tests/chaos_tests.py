"""
Chaos tests (WO8): failure injection against the ingestion layer.

Collected by pytest because pytest.ini lists this module in python_files.

Redis "kill" is simulated by pointing the client at a port with no listener, which
gives the same connection-refused behaviour as a stopped server. Killing a real
container needs the Docker stack, so that variant belongs to the live suite.
"""

import asyncio
import socket
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import redis

from src.ingestion.cache import ResilientCache
from tests.conftest import fake_http_session, routing_http_session

PRIMARY = "https://api.alerts.in.ua/v1/alerts/active.json"
BACKUP = "https://backup.alerts.example/v1/alerts/active.json"


def _closed_port() -> int:
    """Return a local port with no listener."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_connection_failure_does_not_crash_run_loop(make_poller) -> None:
    """A network error from alerts.in.ua is logged and the poll loop survives."""
    poller = make_poller(backoff_max=8.0)

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientConnectionError("blocked"))
    session_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=session_cm):
        # _poll_and_publish swallows non-rate-limit errors; it must not raise.
        asyncio.run(poller._poll_and_publish())


def test_blocked_endpoint_backoff_is_capped(make_poller) -> None:
    """Sustained 429s back off exponentially and stop at backoff_max."""
    poller = make_poller(backoff_max=4.0)

    with patch("aiohttp.ClientSession", return_value=fake_http_session(429)), patch(
        "src.ingestion.alerts_in_ua_poller.asyncio.sleep", new=AsyncMock()
    ) as sleep:
        for _ in range(6):
            asyncio.run(poller._poll_and_publish())

    assert [c.args[0] for c in sleep.await_args_list][-1] == 4.0


def test_blocked_primary_fails_over_to_backup_endpoint(make_poller) -> None:
    """Connection refused by the primary is followed by a successful backup request."""
    poller = make_poller(backup_endpoints=[BACKUP])
    session_cm = routing_http_session(
        {PRIMARY: aiohttp.ClientConnectionError("blocked"), BACKUP: 200}
    )

    with patch("aiohttp.ClientSession", return_value=session_cm):
        alerts = asyncio.run(poller.poll_active_alerts())

    assert alerts == [{"id": 1}]
    urls_called = [c.args[0] for c in session_cm.__aenter__.return_value.get.call_args_list]
    assert urls_called == [PRIMARY, BACKUP]


def test_primary_5xx_fails_over_but_rate_limit_does_not(make_poller) -> None:
    """A 503 from the primary fails over; a 429 backs off without touching the backup."""
    poller = make_poller(backup_endpoints=[BACKUP])
    session_cm = routing_http_session({PRIMARY: 503, BACKUP: 200})
    with patch("aiohttp.ClientSession", return_value=session_cm):
        assert asyncio.run(poller.poll_active_alerts()) == [{"id": 1}]

    poller = make_poller(backup_endpoints=[BACKUP])
    session_cm = routing_http_session({PRIMARY: 429, BACKUP: 200})
    with patch("aiohttp.ClientSession", return_value=session_cm):
        try:
            asyncio.run(poller.poll_active_alerts())
            raised = False
        except Exception as e:  # rate limit is raised as a plain Exception
            raised = "Rate limit" in str(e)
    assert raised
    urls_called = [c.args[0] for c in session_cm.__aenter__.return_value.get.call_args_list]
    assert urls_called == [PRIMARY]


def test_redis_killed_falls_back_to_memory(caplog) -> None:
    """With Redis unreachable, writes and reads still work in memory and a warning is logged."""
    client = redis.Redis(host="127.0.0.1", port=_closed_port(), socket_connect_timeout=1)
    cache = ResilientCache(client)

    start = time.monotonic()
    cache.set("alerts:last", {"count": 3})
    detection_s = time.monotonic() - start

    assert detection_s < 2.0
    assert cache.degraded
    assert cache.get("alerts:last") == {"count": 3}
    assert "falling back to in-memory cache" in caplog.text
