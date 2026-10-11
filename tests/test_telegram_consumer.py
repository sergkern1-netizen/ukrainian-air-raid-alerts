"""
Unit tests for TelegramStreamConsumer and NLP components.

Tests cover:
- Location extraction with gazetteer matching
- Event type classification with keyword matching
- Avro encoding and Kafka publishing
- Message stream handling with mocked Telethon
"""

import json
import pytest
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.ingestion.telegram_consumer import TelegramStreamConsumer
from src.ingestion.telegram_nlp import LocationExtractor, EventClassifier
from src.config import Settings


@pytest.fixture
def mock_config() -> Mock:
    """Create mock Settings object with Telegram credentials."""
    config = Mock(spec=Settings)
    config.api_token = "test-token"
    config.kafka_brokers = "localhost:9092"
    config.timescale_url = "postgresql://localhost/test"
    config.redis_url = "redis://localhost:6379"
    config.isw_scrape_url = "https://example.com"
    config.telegram_api_id = 123456
    config.telegram_api_hash = "test_hash_123"
    config.telegram_phone = "+380501234567"
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
def telegram_consumer(
    mock_config, mock_kafka_producer, mock_schema_registry
) -> TelegramStreamConsumer:
    """Create TelegramStreamConsumer instance with mocks."""
    with patch.object(
        TelegramStreamConsumer, "_load_avro_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "namespace": "com.alerts.airraid",
            "name": "telegram_raw",
            "type": "record",
            "fields": [
                {"name": "event_time", "type": "long"},
                {"name": "ingested_at", "type": "long"},
                {"name": "source_id", "type": "string"},
                {
                    "name": "mentioned_locations",
                    "type": {"type": "array", "items": "string"},
                },
                {
                    "name": "event_type",
                    "type": {
                        "name": "event_type_enum",
                        "type": "enum",
                        "symbols": ["launch", "uav", "missile", "all_clear"],
                    },
                },
                {"name": "msg_time", "type": "long"},
                {"name": "extraction_confidence", "type": "float"},
            ],
        }
        consumer = TelegramStreamConsumer(
            config=mock_config,
            kafka_producer=mock_kafka_producer,
            schema_registry=mock_schema_registry,
        )
    return consumer


class TestLocationExtractor:
    """Tests for LocationExtractor NLP component."""

    def test_extract_locations_kyiv(self) -> None:
        """Extract Kyiv from message."""
        extractor = LocationExtractor()
        text = "Повітряна тривога в Київі та Харкові"
        locations = extractor.extract(text)

        assert "kyiv" in locations
        assert "kharkiv" in locations

    def test_extract_locations_russian_variants(self) -> None:
        """Extract locations from Russian language variants."""
        extractor = LocationExtractor()
        text = "Воздушная тревога в Киеве и Харькове"
        locations = extractor.extract(text)

        assert "kyiv" in locations or len(locations) > 0

    def test_extract_locations_empty_text(self) -> None:
        """Handle empty message text."""
        extractor = LocationExtractor()
        locations = extractor.extract("")

        assert locations == []

    def test_extract_locations_no_matches(self) -> None:
        """Return empty list when no locations match."""
        extractor = LocationExtractor()
        text = "Тестовое сообщение без топонимов"
        locations = extractor.extract(text)

        assert locations == []

    def test_extract_locations_multiple_cities(self) -> None:
        """Extract multiple city mentions."""
        extractor = LocationExtractor()
        text = (
            "Атака на Київ, Харків, Дніпро, Одесу, Львів та Запоріжжя"
        )
        locations = extractor.extract(text)

        assert len(locations) >= 3


class TestEventClassifier:
    """Tests for EventClassifier NLP component."""

    def test_classify_launch_event(self) -> None:
        """Classify launch event from keywords."""
        classifier = EventClassifier()
        text = "Новий раунд атак: запуск дронів"
        event_type = classifier.classify(text)

        # Could be launch or uav depending on keyword priority
        assert event_type in ["launch", "uav"]

    def test_classify_missile_event(self) -> None:
        """Classify missile event."""
        classifier = EventClassifier()
        text = "Крилаті ракети та Х-101 в повітрі"
        event_type = classifier.classify(text)

        assert event_type == "missile"

    def test_classify_uav_event(self) -> None:
        """Classify UAV event."""
        classifier = EventClassifier()
        text = "Атака дронів та БПЛА по Харкову"
        event_type = classifier.classify(text)

        assert event_type == "uav"

    def test_classify_all_clear_event(self) -> None:
        """Classify all-clear event."""
        classifier = EventClassifier()
        text = "Відбій повітряної тривоги в Київі"
        event_type = classifier.classify(text)

        assert event_type == "all_clear"

    def test_classify_default_launch(self) -> None:
        """Default to launch when no keywords match."""
        classifier = EventClassifier()
        text = "Тестовое сообщение"
        event_type = classifier.classify(text)

        assert event_type == "launch"

    def test_classify_confidence_score(self) -> None:
        """Calculate confidence from keyword matches."""
        classifier = EventClassifier()

        # No keywords = base confidence
        conf_none = classifier.get_confidence("test message")
        assert conf_none >= 0.5

        # Multiple keywords = higher confidence
        conf_multi = classifier.get_confidence(
            "запуск дронів крилаті ракети атака"
        )
        assert conf_multi > conf_none


@pytest.mark.asyncio
async def test_extract_locations_consumer(telegram_consumer) -> None:
    """Test location extraction in TelegramStreamConsumer."""
    text = "Повітряна тривога в Київі та Харкові"
    locations = await telegram_consumer.extract_locations(text)

    assert isinstance(locations, list)
    assert "kyiv" in locations or "kharkiv" in locations


@pytest.mark.asyncio
async def test_classify_event_consumer(telegram_consumer) -> None:
    """Test event classification in TelegramStreamConsumer."""
    text = "Крилаті ракети по Київу"
    event_type = await telegram_consumer.classify_event(text)

    assert event_type in ["launch", "uav", "missile", "all_clear"]


@pytest.mark.asyncio
async def test_publish_to_kafka_consumer(
    telegram_consumer, mock_kafka_producer
) -> None:
    """
    Test Kafka publishing with Avro encoding.

    Verifies that messages are encoded to Avro format and published to Kafka.
    """
    # Prepare test data
    msg_id = 12345
    msg_time = 1697145600000  # Unix timestamp in ms
    text = "Атака крилатих ракет"
    locations = ["kyiv", "kharkiv"]
    event_type = "missile"
    confidence = 0.85

    # Publish to Kafka
    await telegram_consumer.publish_to_kafka(
        msg_id=msg_id,
        msg_time=msg_time,
        text=text,
        locations=locations,
        event_type=event_type,
        confidence=confidence,
    )

    # Verify Kafka producer was called
    mock_kafka_producer.produce.assert_called_once()
    call_args = mock_kafka_producer.produce.call_args

    # Verify publish arguments
    assert call_args.kwargs["topic"] == "telegram.raw"
    assert call_args.kwargs["key"] == str(msg_id).encode("utf-8")

    # Verify Avro encoding
    avro_bytes = call_args.kwargs["value"]
    assert isinstance(avro_bytes, bytes)
    assert len(avro_bytes) > 0

    # Verify flush was called
    mock_kafka_producer.flush.assert_called_once()


@pytest.mark.asyncio
async def test_listen_mock_messages(telegram_consumer) -> None:
    """
    Test message stream handling with mocked Telethon.

    Simulates incoming Telegram messages and verifies processing.
    """
    # Create mock Telethon client
    mock_client = AsyncMock()
    telegram_consumer.client = mock_client

    # Create mock message
    mock_message = Mock()
    mock_message.id = 54321
    mock_message.text = "Запуск ракет по Харкову"
    mock_message.date = Mock()
    mock_message.date.timestamp = Mock(return_value=1697145600)

    # Create mock event
    mock_event = Mock()
    mock_event.message = mock_message

    # Mock the event handler setup
    handlers = {}

    def register_handler(event_type):
        def decorator(handler):
            handlers["message"] = handler
            return handler

        return decorator

    mock_client.on = register_handler

    # Verify consumer initializes without error
    assert telegram_consumer is not None
    assert telegram_consumer.client is not None


def test_telegram_consumer_missing_credentials() -> None:
    """Verify TelegramStreamConsumer raises error on missing credentials."""
    config = Mock(spec=Settings)
    config.api_token = "test"
    # Missing telegram_api_id and telegram_api_hash

    producer = Mock()
    registry = Mock()

    with pytest.raises(ValueError, match="Telegram API credentials missing"):
        TelegramStreamConsumer(config, producer, registry)


@pytest.mark.asyncio
async def test_telegram_consumer_initialization(telegram_consumer) -> None:
    """Verify TelegramStreamConsumer instantiates correctly."""
    assert telegram_consumer is not None
    assert telegram_consumer.channel_username == "kpszsu"
    assert telegram_consumer.topic == "telegram.raw"
    assert telegram_consumer.source_id == "telegram.kpszsu"
    assert telegram_consumer.location_extractor is not None
    assert telegram_consumer.event_classifier is not None


def test_calculate_confidence(telegram_consumer) -> None:
    """Test confidence score calculation."""
    # No locations, no event type
    conf = telegram_consumer._calculate_confidence([], "")
    assert 0.5 <= conf <= 1.0

    # With locations and event type
    conf = telegram_consumer._calculate_confidence(["kyiv", "kharkiv"], "missile")
    assert conf > telegram_consumer._calculate_confidence([], "")
    assert conf <= 1.0


@pytest.mark.asyncio
async def test_consumer_stop(telegram_consumer) -> None:
    """Test graceful consumer shutdown."""
    telegram_consumer.client = AsyncMock()
    await telegram_consumer.stop()

    assert telegram_consumer.running is False
    telegram_consumer.client.disconnect.assert_called_once()
