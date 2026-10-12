"""
Shared fixtures and live-test gating for load and chaos tests.

Live tests (real alerts.in.ua, Redis, Kafka) are opt-in: set RUN_LOAD_TESTS=1
and bring up the stack with `docker compose up -d`. Without it they are skipped,
so the default `pytest` run stays offline.
"""

import os
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.ingestion.alerts_in_ua_poller import AsyncAlertsPoller

LIVE_ENABLED = os.getenv("RUN_LOAD_TESTS") == "1"
live_only = pytest.mark.skipif(not LIVE_ENABLED, reason="set RUN_LOAD_TESTS=1 to run live tests")


@pytest.fixture
def make_poller() -> Callable[..., AsyncAlertsPoller]:
    """Factory for AsyncAlertsPoller with mocked Kafka and schema registry."""

    def _make(**kwargs: Any) -> AsyncAlertsPoller:
        config = Mock()
        config.api_token = "test-token"
        config.kafka_brokers = "localhost:9092"
        with patch.object(AsyncAlertsPoller, "_load_avro_schema", return_value={}):
            return AsyncAlertsPoller(
                config=config,
                kafka_producer=Mock(),
                schema_registry=Mock(),
                **kwargs,
            )

    return _make


def fake_http_session(status: int) -> MagicMock:
    """Build an aiohttp.ClientSession stand-in that returns the given HTTP status."""
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value={"alerts": []})
    response.raise_for_status = MagicMock()

    get_cm = MagicMock()
    get_cm.__aenter__ = AsyncMock(return_value=response)
    get_cm.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=get_cm)

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    return session_cm
