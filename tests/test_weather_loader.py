"""
Unit tests for WeatherLoader.

Tests cover:
- Mock API fetching with valid response
- JSON response parsing and schema normalization
- Kafka Avro encoding and publishing
- Hourly scheduling timing
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from src.ingestion.weather_loader import WeatherLoader
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
    return Mock()


@pytest.fixture
def loader(mock_config, mock_kafka_producer, mock_schema_registry) -> WeatherLoader:
    """Create WeatherLoader instance with mocks."""
    with patch.object(WeatherLoader, "_load_avro_schema") as mock_schema:
        mock_schema.return_value = {
            "namespace": "com.alerts.airraid",
            "name": "weather_raw",
            "type": "record",
            "fields": [
                {"name": "event_time", "type": "long"},
                {"name": "ingested_at", "type": "long"},
                {"name": "source_id", "type": "string"},
                {"name": "pressure", "type": "float"},
                {"name": "wind_speed", "type": "float"},
                {"name": "cloud_cover", "type": "float"},
                {"name": "convective_potential", "type": ["null", "float"], "default": None},
                {"name": "visibility", "type": "float"},
            ],
        }
        loader = WeatherLoader(
            config=mock_config,
            kafka_producer=mock_kafka_producer,
            schema_registry=mock_schema_registry,
        )
    return loader


@pytest.mark.asyncio
async def test_fetch_forecast_mocked(loader: WeatherLoader) -> None:
    """
    Test fetching weather forecast with mocked HTTP response.

    Verifies that valid JSON response is returned and logged correctly.
    """
    mock_api_response = {
        "latitude": 50.45,
        "longitude": 30.52,
        "timezone": "UTC",
        "hourly": {
            "time": [
                "2026-10-12T10:00Z",
                "2026-10-12T11:00Z",
                "2026-10-12T12:00Z",
            ],
            "temperature_2m": [15.2, 16.1, 17.5],
            "wind_speed_10m": [3.5, 4.2, 3.8],
            "cloud_cover": [45.0, 50.0, 55.0],
            "cape": [150.5, 175.3, 200.1],
            "visibility": [10000, 10000, 9500],
        },
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_api_response)
        mock_response_obj.__aenter__.return_value = mock_response_obj
        mock_response_obj.__aexit__.return_value = None

        mock_get.return_value = mock_response_obj

        result = await loader.fetch_forecast()

        assert result is not None
        assert result["latitude"] == 50.45
        assert result["longitude"] == 30.52
        assert len(result["hourly"]["time"]) == 3
        assert result["hourly"]["temperature_2m"] == [15.2, 16.1, 17.5]


@pytest.mark.asyncio
async def test_parse_response(loader: WeatherLoader) -> None:
    """
    Test parsing Open-Meteo API response to schema.

    Verifies that 2D array response is correctly mapped to weather_raw schema
    with proper timestamp conversion and default values.
    """
    api_response = {
        "latitude": 50.45,
        "longitude": 30.52,
        "timezone": "UTC",
        "hourly": {
            "time": [
                "2026-10-12T10:00Z",
                "2026-10-12T11:00Z",
            ],
            "temperature_2m": [15.2, 16.1],
            "wind_speed_10m": [3.5, 4.2],
            "cloud_cover": [45.0, 50.0],
            "cape": [150.5, 175.3],
            "visibility": [10000, 10000],
        },
    }

    records = await loader.parse_response(api_response)

    assert len(records) == 2

    # Check first record
    record_1 = records[0]
    assert record_1["source_id"] == "openmeteo"
    assert record_1["wind_speed"] == 3.5
    assert record_1["cloud_cover"] == 45.0
    assert record_1["convective_potential"] == 150.5
    assert record_1["visibility"] == 10000
    assert record_1["pressure"] == 1013.25  # Default estimate
    assert "event_time" in record_1
    assert isinstance(record_1["event_time"], int)
    assert record_1["event_time"] > 0
    assert "ingested_at" in record_1

    # Check second record
    record_2 = records[1]
    assert record_2["wind_speed"] == 4.2
    assert record_2["cloud_cover"] == 50.0
    assert record_2["convective_potential"] == 175.3


@pytest.mark.asyncio
async def test_publish_to_kafka(loader: WeatherLoader) -> None:
    """
    Test Kafka publishing with Avro encoding.

    Verifies that weather records are encoded to Avro binary format and
    published to Kafka with correct topic and key.
    """
    records = [
        {
            "event_time": 1697097600000,
            "ingested_at": 1697097605000,
            "source_id": "openmeteo",
            "pressure": 1013.25,
            "wind_speed": 3.5,
            "cloud_cover": 45.0,
            "convective_potential": 150.5,
            "visibility": 10000,
        },
    ]

    await loader.publish_to_kafka(records)

    loader.kafka_producer.produce.assert_called_once()
    call_kwargs = loader.kafka_producer.produce.call_args[1]

    assert call_kwargs["topic"] == "weather.raw"
    assert call_kwargs["key"] == b"1697097600000"
    assert isinstance(call_kwargs["value"], bytes)
    assert len(call_kwargs["value"]) > 0

    loader.kafka_producer.flush.assert_called_once()


@pytest.mark.asyncio
async def test_run_hourly_timing(loader: WeatherLoader) -> None:
    """
    Test hourly scheduling without real API/Kafka calls.

    Verifies that run_hourly respects sleep interval and can be cancelled.
    Does not make actual HTTP calls or Kafka publishes.
    """
    # Mock fetch_forecast and publish_to_kafka
    loader.fetch_forecast = AsyncMock(
        return_value={
            "hourly": {
                "time": ["2026-10-12T10:00Z"],
                "temperature_2m": [15.0],
                "wind_speed_10m": [3.0],
                "cloud_cover": [40.0],
                "cape": [100.0],
                "visibility": [10000],
            }
        }
    )
    loader.publish_to_kafka = AsyncMock()
    loader.parse_response = AsyncMock(
        return_value=[
            {
                "event_time": 1697097600000,
                "ingested_at": 1697097605000,
                "source_id": "openmeteo",
                "pressure": 1013.25,
                "wind_speed": 3.0,
                "cloud_cover": 40.0,
                "convective_potential": 100.0,
                "visibility": 10000,
            }
        ]
    )

    # Create a task and cancel it after a short delay
    run_task = asyncio.create_task(loader.run_hourly())

    # Let it start
    await asyncio.sleep(0.1)

    # Verify it's running
    assert loader.running is True
    assert loader.fetch_forecast.called

    # Cancel the task
    run_task.cancel()
    try:
        await run_task
    except asyncio.CancelledError:
        pass

    # Verify it stopped
    assert loader.running is False


@pytest.mark.asyncio
async def test_instantiation(
    mock_config: Settings,
    mock_kafka_producer: Mock,
    mock_schema_registry: Mock,
) -> None:
    """
    Test WeatherLoader instantiation without error.

    Verifies initialization with config, producer, and schema registry.
    """
    with patch.object(WeatherLoader, "_load_avro_schema") as mock_schema:
        mock_schema.return_value = {
            "type": "record",
            "name": "weather_raw",
            "fields": [],
        }

        loader = WeatherLoader(
            config=mock_config,
            kafka_producer=mock_kafka_producer,
            schema_registry=mock_schema_registry,
        )

        assert loader.config == mock_config
        assert loader.kafka_producer == mock_kafka_producer
        assert loader.schema_registry == mock_schema_registry
        assert loader.api_endpoint == "https://api.open-meteo.com/v1/forecast"
        assert loader.topic == "weather.raw"
        assert loader.source_id == "openmeteo"
        assert loader.latitude == 50.45
        assert loader.longitude == 30.52
        assert loader.running is False
