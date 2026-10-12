"""
Chaos tests (WO8): failure injection against the ingestion layer.

Collected by pytest because pytest.ini lists this module in python_files.

Implemented:
- alerts.in.ua blocked (HTTP 429 / connection error): poller backs off, does not crash.

Not yet implemented in src/ (recorded as expected failures, not silently passed):
- Redis killed -> in-memory fallback: no Redis client exists in src/ yet.
- alerts.in.ua blocked -> backup endpoint failover: poller has a single endpoint.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from tests.conftest import fake_http_session


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

    assert poller.backoff_delay == 4.0


@pytest.mark.xfail(strict=True, reason="No Redis client / in-memory fallback in src/ yet (WO8 gap)")
def test_redis_killed_falls_back_to_memory() -> None:
    """Killing Redis triggers a logged warning and an in-memory fallback cache."""
    from src.ingestion import cache  # noqa: F401  # module does not exist yet


@pytest.mark.xfail(strict=True, reason="Single alerts.in.ua endpoint; no backup failover (WO8 gap)")
def test_blocked_primary_fails_over_to_backup_endpoint() -> None:
    """Blocking the primary endpoint switches polling to the backup stub."""
    from src.ingestion.alerts_in_ua_poller import AsyncAlertsPoller

    assert hasattr(AsyncAlertsPoller, "backup_endpoint")
