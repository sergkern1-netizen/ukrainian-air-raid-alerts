"""
Unit tests for AsyncAlertsPoller.

Tests cover:
- Mock API polling with valid response
- Kafka Avro encoding and publishing
- 429 rate limit exponential backoff
- Standby/active failover via leader election
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.ingestion.alerts_in_ua_poller import AsyncAlertsPoller
from src.config import Settings


@pytest.fixture
def mock_config() -> Settings:
    """Create mock Settings object."""
    config = Mock(spec=Settings)
    config.api_token = "test-token"
    config.kafka_brokers = "localhost:9092"
    config.timescale_url = "postgresql://localhost/test"
    config.redis_url = "redis://localhost:6379"
    config.isw_scrape_url = "https://example.com"
    return config


@pytest.fixture
def mock_kafka_producer() -> Mock:
    """Create mock Kafka producer."""
    producer = Mock()
    producer.produce = Mock()
    producer.flush = Mock()
    return producer


@pytest.fixture
def mock_schema_registry() -> Mock:
    """Create mock schema registry client."""
    registry = Mock()
    registry.register_schema.return_value = 1
    return registry


@pytest.fixture
def poller(mock_config, mock_kafka_producer, mock_schema_registry) -> AsyncAlertsPoller:
    """Create AsyncAlertsPoller instance with mocks."""
    with patch.object(AsyncAlertsPoller, "_load_avro_schema") as mock_schema:
        mock_schema.return_value = {
            "type": "record",
            "name": "alerts_raw",
            "fields": [
                {"name": "event_time", "type": "long"},
                {"name": "ingested_at", "type": "long"},
                {"name": "source_id", "type": "string"},
                {"name": "alert_count_15m", "type": "int"},
                {"name": "alert_count_1h", "type": "int"},
                {"name": "alert_count_6h", "type": "int"},
                {"name": "alert_count_24h", "type": "int"},
                {"name": "active_flag", "type": "boolean"},
                {"name": "oblast", "type": ["null", "string"], "default": None},
                {"name": "h3", "type": ["null", "string"], "default": None},
                {"name": "duration", "type": ["null", "int"], "default": None},
                {
                    "name": "time_since_last_alert",
                    "type": ["null", "int"],
                    "default": None,
                },
                {"name": "neighbor_active_count", "type": "int"},
                {"name": "inferred_end_flag", "type": "boolean"},
            ],
        }
        poller = AsyncAlertsPoller(
            config=mock_config,
            kafka_producer=mock_kafka_producer,
            schema_registry=mock_schema_registry,
        )
    return poller


@pytest.mark.asyncio
async def test_poll_active_alerts_mocked(poller: AsyncAlertsPoller) -> None:
    """
    Test polling API with mocked HTTP response.

    Verifies that valid JSON response is parsed and returned as list of alerts.
    """
    mock_response = {
        "alerts": [
            {
                "id": "alert-1",
                "location_title": "Kyiv",
                "started_at": "2026-10-12T10:00:00Z",
                "finished_at": None,
                "alert_type": "missile",
            },
            {
                "id": "alert-2",
                "location_title": "Kharkiv",
                "started_at": "2026-10-12T10:05:00Z",
                "finished_at": None,
                "alert_type": "missile",
            },
        ]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_response_obj.__aenter__.return_value = mock_response_obj
        mock_response_obj.__aexit__.return_value = None

        mock_get.return_value = mock_response_obj

        alerts = await poller.poll_active_alerts()

        assert len(alerts) == 2
        assert alerts[0]["id"] == "alert-1"
        assert alerts[0]["location_title"] == "Kyiv"
        assert alerts[1]["id"] == "alert-2"
        assert alerts[1]["location_title"] == "Kharkiv"


@pytest.mark.asyncio
async def test_publish_to_kafka(poller: AsyncAlertsPoller) -> None:
    """
    Test Kafka publishing with Avro encoding.

    Verifies that alerts are encoded to Avro binary format and published
    to Kafka with correct topic and key.
    """
    alerts = [
        {
            "id": "alert-1",
            "location_title": "Kyiv",
            "started_at": "2026-10-12T10:00:00Z",
        },
    ]

    await poller.publish_to_kafka(alerts)

    poller.kafka_producer.produce.assert_called_once()
    call_kwargs = poller.kafka_producer.produce.call_args[1]

    assert call_kwargs["topic"] == "alerts.raw"
    assert call_kwargs["key"] == b"alert-1"
    assert isinstance(call_kwargs["value"], bytes)
    assert len(call_kwargs["value"]) > 0

    poller.kafka_producer.flush.assert_called_once()


@pytest.mark.asyncio
async def test_429_exponential_backoff(poller: AsyncAlertsPoller) -> None:
    """
    Test exponential backoff on HTTP 429 (rate limit).

    Verifies that backoff delay doubles on each 429 response, up to max of 60s.
    """
    initial_backoff = poller.backoff_delay
    assert initial_backoff == 1.0

    # Simulate first 429
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 429
        mock_response_obj.__aenter__.return_value = mock_response_obj
        mock_response_obj.__aexit__.return_value = None
        mock_get.return_value = mock_response_obj

        with pytest.raises(Exception, match="Rate limit"):
            await poller.poll_active_alerts()

        assert poller.backoff_delay == 2.0

    # Simulate second 429
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 429
        mock_response_obj.__aenter__.return_value = mock_response_obj
        mock_response_obj.__aexit__.return_value = None
        mock_get.return_value = mock_response_obj

        with pytest.raises(Exception, match="Rate limit"):
            await poller.poll_active_alerts()

        assert poller.backoff_delay == 4.0

    # Verify backoff caps at 60s
    for _ in range(10):
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 429
            mock_response_obj.__aenter__.return_value = mock_response_obj
            mock_response_obj.__aexit__.return_value = None
            mock_get.return_value = mock_response_obj

            with pytest.raises(Exception, match="Rate limit"):
                await poller.poll_active_alerts()

    assert poller.backoff_delay <= 60.0


@pytest.mark.asyncio
async def test_leader_election_heartbeat(poller: AsyncAlertsPoller) -> None:
    """
    Test standby/active failover via heartbeat timeout.

    Verifies that when active heartbeat is missing >30s, standby becomes active.
    """
    # Start as active
    assert poller.is_active is True

    # Demote to standby
    poller.is_active = False

    # Set heartbeat to >30s ago
    import time

    poller.last_heartbeat = time.time() - 35

    # Call leader election
    await poller._leader_election()

    # Verify promotion to active
    assert poller.is_active is True
    assert poller.backoff_delay == 1.0


@pytest.mark.asyncio
async def test_instantiation(
    mock_config: Settings,
    mock_kafka_producer: Mock,
    mock_schema_registry: Mock,
) -> None:
    """
    Test AsyncAlertsPoller instantiation without error.

    Verifies initialization with config, producer, and schema registry.
    """
    with patch.object(AsyncAlertsPoller, "_load_avro_schema") as mock_schema:
        mock_schema.return_value = {
            "type": "record",
            "name": "alerts_raw",
            "fields": [],
        }

        poller = AsyncAlertsPoller(
            config=mock_config,
            kafka_producer=mock_kafka_producer,
            schema_registry=mock_schema_registry,
        )

        assert poller.config == mock_config
        assert poller.kafka_producer == mock_kafka_producer
        assert poller.schema_registry == mock_schema_registry
        assert poller.poll_interval == 15.0
        assert poller.backoff_max == 60.0
        assert poller.heartbeat_timeout == 30.0
        assert poller.is_active is True
        assert poller.running is False
