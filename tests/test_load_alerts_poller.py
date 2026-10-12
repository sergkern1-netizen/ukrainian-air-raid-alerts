"""
Load tests for the alerts.in.ua poller (WO8).

Offline tests verify the rate budget and 429 backoff against a mocked HTTP
session. The sustained live test calls the real API and is gated by
RUN_LOAD_TESTS=1.
"""

import asyncio
import inspect
import math
import time
from typing import Callable
from unittest.mock import MagicMock, patch

import pytest

from src.config import config as load_config
from src.ingestion.alerts_in_ua_poller import AsyncAlertsPoller
from tests.conftest import fake_http_session, live_only

MAX_REQUESTS_PER_MINUTE = 4
LIVE_WINDOW_MINUTES = 10


def test_default_poll_interval_stays_within_rate_budget() -> None:
    """Default poll interval must not exceed 4 requests per minute."""
    default = inspect.signature(AsyncAlertsPoller.__init__).parameters["poll_interval"].default
    assert 60.0 / default <= MAX_REQUESTS_PER_MINUTE


def test_429_raises_and_doubles_backoff(make_poller: Callable[..., AsyncAlertsPoller]) -> None:
    """A 429 response raises a rate-limit error and doubles the backoff delay."""
    poller = make_poller(backoff_max=60.0)
    assert poller.backoff_delay == 1.0

    with patch("aiohttp.ClientSession", return_value=fake_http_session(429)):
        with pytest.raises(Exception, match="Rate limit"):
            asyncio.run(poller.poll_active_alerts())

    assert poller.backoff_delay == 2.0


def test_repeated_429_backoff_grows_exponentially_and_caps(
    make_poller: Callable[..., AsyncAlertsPoller],
) -> None:
    """Consecutive 429s double the delay until backoff_max, then stay capped."""
    poller = make_poller(backoff_max=8.0)
    observed = []

    with patch("aiohttp.ClientSession", return_value=fake_http_session(429)):
        for _ in range(5):
            with pytest.raises(Exception, match="Rate limit"):
                asyncio.run(poller.poll_active_alerts())
            observed.append(poller.backoff_delay)

    assert observed == [2.0, 4.0, 8.0, 8.0, 8.0]


def test_successful_poll_returns_alerts(make_poller: Callable[..., AsyncAlertsPoller]) -> None:
    """A 200 response yields the parsed alerts list and does not touch backoff."""
    poller = make_poller()

    with patch("aiohttp.ClientSession", return_value=fake_http_session(200)):
        alerts = asyncio.run(poller.poll_active_alerts())

    assert alerts == []
    assert poller.backoff_delay == 1.0


@live_only
def test_sustained_rate_and_latency_live() -> None:
    """Poll the real API for 10 minutes: <=4 req/min and p99 latency under 1000 ms."""
    cfg = load_config()
    poller = AsyncAlertsPoller(
        config=cfg,
        kafka_producer=MagicMock(),
        schema_registry=MagicMock(),
        poll_interval=60.0 / MAX_REQUESTS_PER_MINUTE,
    )

    latencies = []
    request_times = []
    errors = []
    deadline = time.monotonic() + LIVE_WINDOW_MINUTES * 60

    async def _run() -> None:
        while time.monotonic() < deadline:
            start = time.perf_counter()
            request_times.append(time.monotonic())
            try:
                await poller.poll_active_alerts()
            except Exception as exc:
                # Failures are counted, not hidden: a 401 from an invalid token
                # or a 429 storm must fail this test, not pass it with fake latency.
                errors.append(repr(exc))
            else:
                latencies.append((time.perf_counter() - start) * 1000)
            await asyncio.sleep(poller.poll_interval)

    asyncio.run(_run())

    assert not errors, f"{len(errors)}/{len(request_times)} polls failed; first: {errors[0]}"

    window_minutes = (request_times[-1] - request_times[0]) / 60
    assert len(request_times) / max(window_minutes, 1e-9) <= MAX_REQUESTS_PER_MINUTE + 0.5

    latencies.sort()
    p99 = latencies[max(0, math.ceil(0.99 * len(latencies)) - 1)]
    assert p99 < 1000, f"p99 latency {p99:.0f} ms exceeds 1000 ms"
