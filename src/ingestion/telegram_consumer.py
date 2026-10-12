"""
Async consumer for @kpszsu (Ukrainian Air Force official Telegram channel).

Extracts location mentions (NER + gazetteer matching), classifies event types
(launch, UAV, missile, all-clear), and publishes to telegram.raw Kafka topic
in Avro format.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import avro.io
import avro.schema
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from io import BytesIO
from telethon import TelegramClient
from telethon.events import NewMessage

from src.config import Settings
from src.ingestion.telegram_nlp import EventClassifier, LocationExtractor

logger = logging.getLogger(__name__)


class TelegramStreamConsumer:
    """
    Async consumer for Ukrainian Air Force Telegram channel (@kpszsu).

    Extracts locations and event types from Telegram messages and publishes
    to Kafka in Avro format.

    Attributes:
        config: Application configuration with Telegram API credentials.
        schema_registry: Schema registry client for Avro schema management.
        kafka_producer: Confluent Kafka producer instance.
        client: Telethon TelegramClient instance.
        location_extractor: NER + gazetteer for location extraction.
        event_classifier: Event type classifier (keyword-based).
        topic: Kafka topic name (default: telegram.raw).
    """

    def __init__(
        self,
        config: Settings,
        kafka_producer: Producer,
        schema_registry: SchemaRegistryClient,
    ) -> None:
        """
        Initialize the Telegram stream consumer.

        Args:
            config: Settings object with Telegram API credentials.
            kafka_producer: Confluent Kafka producer.
            schema_registry: Schema registry client for Avro encoding.

        Raises:
            ValueError: If required Telegram API credentials missing.
        """
        self.config = config
        self.kafka_producer = kafka_producer
        self.schema_registry = schema_registry

        # Verify Telegram credentials
        if (
            not hasattr(config, "telegram_api_id")
            or config.telegram_api_id is None
            or not hasattr(config, "telegram_api_hash")
            or config.telegram_api_hash is None
        ):
            raise ValueError(
                "Telegram API credentials missing (telegram_api_id, telegram_api_hash)"
            )

        self.api_id = config.telegram_api_id
        self.api_hash = config.telegram_api_hash
        self.phone = getattr(config, "telegram_phone", None)

        self.channel_username = "kpszsu"
        self.topic = "telegram.raw"
        self.source_id = "telegram.kpszsu"

        self.client: Optional[TelegramClient] = None
        self.location_extractor = LocationExtractor()
        self.event_classifier = EventClassifier()
        self.running = False

        # Load Avro schema
        self.avro_schema = self._load_avro_schema()

    def _load_avro_schema(self) -> Dict[str, Any]:
        """
        Load Avro schema for telegram.raw topic.

        Returns:
            Dict with Avro schema definition.

        Raises:
            FileNotFoundError: If schema file not found.
        """
        schema_path = "src/schemas/telegram_raw.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        return schema

    async def connect(self) -> None:
        """
        Connect to Telegram using Telethon MTProto client.

        Starts a session using API credentials from config.
        Session data is stored in .env or memory.

        Raises:
            RuntimeError: If connection fails.
        """
        try:
            session_name = "telegram_session"
            self.client = TelegramClient(session_name, self.api_id, self.api_hash)

            await self.client.start(phone=self.phone)
            logger.info(
                f"Connected to Telegram as {self.client.get_me().first_name}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}", exc_info=True)
            raise RuntimeError(f"Telegram connection failed: {e}")

    async def listen(self) -> None:
        """
        Main message streaming loop.

        Listens for new messages on @kpszsu channel, extracts locations
        and event types, and publishes to Kafka.
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")

        self.running = True
        logger.info(f"Starting listener on @{self.channel_username}")

        @self.client.on(NewMessage(chats=[self.channel_username]))
        async def handler(event: NewMessage) -> None:
            """Handle incoming messages."""
            try:
                await self._process_message(event)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

        try:
            await self.client.run_until_disconnected()
        except asyncio.CancelledError:
            logger.info("Listener cancelled")
            self.running = False
        except Exception as e:
            logger.error(f"Listener error: {e}", exc_info=True)
            self.running = False

    async def _process_message(self, event: NewMessage) -> None:
        """
        Process incoming Telegram message.

        Extracts locations, classifies event type, and publishes to Kafka.

        Args:
            event: Telethon NewMessage event.
        """
        msg = event.message
        text = msg.text or ""

        if not text.strip():
            logger.debug("Skipping empty message")
            return

        logger.info(f"Processing message: {text[:50]}...")

        # Extract locations and classify event
        locations = await self.extract_locations(text)
        event_type = await self.classify_event(text)

        confidence = self._calculate_confidence(text)

        # Publish to Kafka
        await self.publish_to_kafka(
            msg_id=msg.id,
            msg_time=int(msg.date.timestamp() * 1000),
            text=text,
            locations=locations,
            event_type=event_type,
            confidence=confidence,
        )

    async def extract_locations(self, text: str) -> List[str]:
        """
        Extract location mentions from message text.

        Uses NER + gazetteer matching to identify Ukrainian/Russian toponyms.

        Args:
            text: Message text to extract locations from.

        Returns:
            List of location names (cities, oblasts) found in text.
        """
        try:
            locations = self.location_extractor.extract(text)
            if locations:
                logger.debug(f"Extracted locations: {locations}")
            return locations
        except Exception as e:
            logger.error(f"Location extraction failed: {e}", exc_info=True)
            return []

    async def classify_event(self, text: str) -> str:
        """
        Classify event type from message text.

        Keyword-based classification for launch, UAV, missile, all_clear.

        Args:
            text: Message text to classify.

        Returns:
            Event type (launch, uav, missile, all_clear).
        """
        try:
            event_type = self.event_classifier.classify(text)
            logger.debug(f"Classified event type: {event_type}")
            return event_type
        except Exception as e:
            logger.error(f"Event classification failed: {e}", exc_info=True)
            return "launch"  # Default fallback

    async def publish_to_kafka(
        self,
        msg_id: int,
        msg_time: int,
        text: str,
        locations: List[str],
        event_type: str,
        confidence: float,
    ) -> None:
        """
        Encode message to Avro and publish to Kafka.

        Args:
            msg_id: Telegram message ID.
            msg_time: Message timestamp in milliseconds (Unix time).
            text: Raw message text.
            locations: Extracted location names.
            event_type: Classified event type.
            confidence: Extraction confidence score (0-1).
        """
        try:
            schema = avro.schema.parse(json.dumps(self.avro_schema))
            current_time_ms = int(time.time() * 1000)

            # Build record matching telegram_raw.avsc schema
            record = {
                "event_time": msg_time,
                "ingested_at": current_time_ms,
                "source_id": self.source_id,
                "mentioned_locations": locations,
                "event_type": event_type,
                "msg_time": msg_time,
                "extraction_confidence": confidence,
            }

            # Encode to Avro
            writer = avro.io.DatumWriter(schema)
            bytes_buffer = BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_buffer)
            writer.write(record, encoder)
            avro_bytes = bytes_buffer.getvalue()

            # Publish to Kafka
            self.kafka_producer.produce(
                topic=self.topic,
                key=str(msg_id).encode("utf-8"),
                value=avro_bytes,
                on_delivery=self._delivery_report,
            )

            logger.debug(f"Published message {msg_id} to Kafka")

        except Exception as e:
            logger.error(f"Failed to publish message {msg_id}: {e}", exc_info=True)

        self.kafka_producer.flush(timeout=5)

    def _delivery_report(self, err: Optional[Exception], msg: Any) -> None:
        """
        Kafka delivery callback.

        Args:
            err: Error if delivery failed, None if successful.
            msg: The delivered message.
        """
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(
                f"Message delivered to {msg.topic()} [{msg.partition()}] "
                f"at offset {msg.offset()}"
            )

    def _calculate_confidence(self, text: str) -> float:
        """
        Calculate extraction confidence from the event classifier's keyword matches.

        Confidence is 0.0 when no keyword matched: the published event_type is then
        the schema default ('launch'), not an observation. Locations do not raise
        confidence, because they say nothing about the event type.

        Args:
            text: Raw message text.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        return self.event_classifier.get_confidence(text)

    async def stop(self) -> None:
        """Stop the consumer and disconnect from Telegram."""
        logger.info("Stopping TelegramStreamConsumer")
        self.running = False
        if self.client:
            await self.client.disconnect()
