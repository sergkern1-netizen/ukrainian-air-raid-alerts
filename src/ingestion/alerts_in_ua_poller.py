"""
Async poller for alerts.in.ua API with active/standby failover and Kafka publishing.

Polls every 15 seconds (4 req/min sustainable rate) with exponential backoff on 429.
Implements leader election: standby becomes active if active heartbeat missing >30s.
Publishes Avro-encoded messages to Kafka alerts.raw topic.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from pydantic import BaseModel

from src.config import Settings

logger = logging.getLogger(__name__)


class AlertRecord(BaseModel):
    """Model for individual alert from API response."""

    id: str
    location_title: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    updated_at: Optional[str] = None
    alert_type: Optional[str] = None
    location_uid: Optional[str] = None

    class Config:
        """Allow extra fields from API response."""

        extra = "allow"


class AsyncAlertsPoller:
    """
    Async poller for alerts.in.ua API with leader election and Kafka publishing.

    Attributes:
        config: Application configuration with API token and Kafka brokers.
        kafka_producer: Confluent Kafka producer instance.
        schema_registry: Schema registry client for Avro schema management.
        poll_interval: Polling interval in seconds (default 15s = 4 req/min).
        backoff_max: Maximum backoff delay in seconds (default 60s).
        heartbeat_timeout: Standby election timeout in seconds (default 30s).
    """

    def __init__(
        self,
        config: Settings,
        kafka_producer: Producer,
        schema_registry: SchemaRegistryClient,
        poll_interval: float = 15.0,
        backoff_max: float = 60.0,
        heartbeat_timeout: float = 30.0,
    ) -> None:
        """
        Initialize the async poller.

        Args:
            config: Settings object with api_token and kafka_brokers.
            kafka_producer: Confluent Kafka producer.
            schema_registry: Schema registry client for Avro encoding.
            poll_interval: Seconds between API polls (default 15).
            backoff_max: Maximum exponential backoff delay in seconds.
            heartbeat_timeout: Seconds before standby election triggered.
        """
        self.config = config
        self.kafka_producer = kafka_producer
        self.schema_registry = schema_registry
        self.poll_interval = poll_interval
        self.backoff_max = backoff_max
        self.heartbeat_timeout = heartbeat_timeout

        self.api_endpoint = "https://api.alerts.in.ua/v1/alerts/active.json"
        self.topic = "alerts.raw"
        self.source_id = "alerts.in.ua"

        self.is_active = True
        self.last_heartbeat = time.time()
        self.backoff_delay = 1.0
        self.running = False

        # Load Avro schema
        self.avro_schema = self._load_avro_schema()

    def _load_avro_schema(self) -> Dict[str, Any]:
        """
        Load Avro schema for alerts.raw topic.

        Returns:
            Dict with Avro schema definition.

        Raises:
            FileNotFoundError: If schema file not found.
        """
        import json

        schema_path = "src/schemas/alerts_raw.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        return schema

    async def run(self) -> None:
        """
        Main polling loop.

        Continuously polls API every poll_interval seconds, handles rate limits
        with exponential backoff, and performs leader election for standby failover.
        """
        self.running = True
        logger.info(
            f"AsyncAlertsPoller starting. Active={self.is_active}, "
            f"Poll interval={self.poll_interval}s"
        )

        try:
            while self.running:
                try:
                    await self._leader_election()

                    if self.is_active:
                        await self._poll_and_publish()
                        self.last_heartbeat = time.time()
                        self.backoff_delay = 1.0

                    await asyncio.sleep(self.poll_interval)

                except asyncio.CancelledError:
                    logger.info("Poller cancelled")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in poll loop: {e}", exc_info=True)
                    await asyncio.sleep(min(self.backoff_delay, self.backoff_max))
                    self.backoff_delay *= 2

        finally:
            self.running = False
            logger.info("AsyncAlertsPoller stopped")

    async def _leader_election(self) -> None:
        """
        Perform leader election check.

        If active instance heartbeat is missing >heartbeat_timeout seconds,
        current standby becomes active (simulating Kubernetes lease election).
        """
        if not self.is_active:
            time_since_heartbeat = time.time() - self.last_heartbeat
            if time_since_heartbeat > self.heartbeat_timeout:
                self.is_active = True
                self.backoff_delay = 1.0
                logger.info(
                    f"Standby promoted to active (heartbeat timeout={time_since_heartbeat:.1f}s)"
                )

    async def poll_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Fetch active alerts from alerts.in.ua API.

        Returns:
            List of alert dictionaries from API response.

        Raises:
            aiohttp.ClientError: On HTTP errors.
            asyncio.TimeoutError: On request timeout.
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "User-Agent": "AlertsPoller/1.0",
        }

        timeout = aiohttp.ClientTimeout(total=10.0)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(self.api_endpoint, headers=headers) as response:
                if response.status == 429:
                    logger.warning("Rate limit hit (429). Applying exponential backoff")
                    self.backoff_delay = min(self.backoff_delay * 2, self.backoff_max)
                    raise Exception("Rate limit (429)")

                response.raise_for_status()

                data = await response.json()
                alerts = data.get("alerts", [])

                logger.info(f"Polled {len(alerts)} active alerts")
                return alerts

    async def publish_to_kafka(self, alerts: List[Dict[str, Any]]) -> None:
        """
        Encode alerts to Avro and publish to Kafka.

        Each alert record is encoded using the alerts_raw Avro schema and
        published to the alerts.raw topic.

        Args:
            alerts: List of alert dictionaries from API.
        """
        import avro.io
        import avro.schema
        from io import BytesIO

        schema = avro.schema.parse(json.dumps(self.avro_schema))

        current_time_ms = int(time.time() * 1000)

        for alert in alerts:
            try:
                # Build record matching Avro schema
                record = {
                    "event_time": current_time_ms,
                    "ingested_at": current_time_ms,
                    "source_id": self.source_id,
                    "alert_count_15m": 1,
                    "alert_count_1h": 1,
                    "alert_count_6h": 1,
                    "alert_count_24h": 1,
                    "active_flag": True,
                    "oblast": alert.get("location_title"),
                    "h3": None,
                    "duration": None,
                    "time_since_last_alert": None,
                    "neighbor_active_count": 0,
                    "inferred_end_flag": False,
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
                    key=alert.get("id", "unknown").encode("utf-8"),
                    value=avro_bytes,
                    on_delivery=self._delivery_report,
                )

            except Exception as e:
                logger.error(f"Failed to publish alert {alert.get('id')}: {e}")

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
            logger.debug(
                f"Message delivered to {msg.topic()} [{msg.partition()}] "
                f"at offset {msg.offset()}"
            )

    async def _poll_and_publish(self) -> None:
        """
        Poll API and publish to Kafka.

        Handles rate limit backoff (429 responses).
        """
        try:
            alerts = await self.poll_active_alerts()
            if alerts:
                await self.publish_to_kafka(alerts)
        except Exception as e:
            if "Rate limit" in str(e):
                await asyncio.sleep(min(self.backoff_delay, self.backoff_max))
            else:
                logger.error(f"Poll and publish failed: {e}")

    async def stop(self) -> None:
        """Stop the polling loop gracefully."""
        logger.info("Stopping AsyncAlertsPoller")
        self.running = False
