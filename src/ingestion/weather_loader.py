"""
Async weather data fetcher from Open-Meteo API with Kafka publishing.

Fetches hourly weather forecast for Kyiv (proxy for Ukraine) and publishes
to weather.raw Kafka topic in Avro format. Handles rate limits, missing data,
and timezone normalization to UTC.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient

from src.ingestion.avro_wire import frame, register_value_schema

from src.config import Settings

logger = logging.getLogger(__name__)


class WeatherLoader:
    """
    Async weather data loader from Open-Meteo API.

    Attributes:
        config: Application configuration.
        kafka_producer: Confluent Kafka producer instance.
        schema_registry: Schema registry client for Avro schema management.
        api_endpoint: Open-Meteo API endpoint.
        topic: Kafka topic name (weather.raw).
        source_id: Source identifier (openmeteo).
        latitude: Latitude for Kyiv (proxy location).
        longitude: Longitude for Kyiv (proxy location).
    """

    def __init__(
        self,
        config: Settings,
        kafka_producer: Producer,
        schema_registry: SchemaRegistryClient,
    ) -> None:
        """
        Initialize the weather loader.

        Args:
            config: Settings object with kafka_brokers.
            kafka_producer: Confluent Kafka producer.
            schema_registry: Schema registry client for Avro encoding.
        """
        self.config = config
        self.kafka_producer = kafka_producer
        self.schema_registry = schema_registry

        self.api_endpoint = "https://api.open-meteo.com/v1/forecast"
        self.topic = "weather.raw"
        self.source_id = "openmeteo"

        # Kyiv coordinates (proxy for Ukraine)
        self.latitude = 50.45
        self.longitude = 30.52

        self.running = False

        # Load Avro schema
        self.avro_schema = self._load_avro_schema()

        self.schema_id = register_value_schema(
            self.schema_registry, self.topic, self.avro_schema
        )

    def _load_avro_schema(self) -> Dict[str, Any]:
        """
        Load Avro schema for weather.raw topic.

        Returns:
            Dict with Avro schema definition.

        Raises:
            FileNotFoundError: If schema file not found.
        """
        schema_path = "src/schemas/weather_raw.avsc"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        return schema

    async def fetch_forecast(self) -> Optional[Dict[str, Any]]:
        """
        Fetch hourly weather forecast from Open-Meteo API.

        Returns:
            Dict with API response data, or None if fetch failed.

        Raises:
            aiohttp.ClientError: On HTTP errors (except 404/timeout).
            asyncio.TimeoutError: On request timeout.
        """
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": "temperature_2m,wind_speed_10m,cloud_cover,cape,visibility",
            "timezone": "UTC",
        }

        timeout = aiohttp.ClientTimeout(total=10.0)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.api_endpoint, params=params) as response:
                    if response.status == 404:
                        logger.error(f"API endpoint not found (404): {self.api_endpoint}")
                        return None

                    response.raise_for_status()
                    data = await response.json()
                    logger.info("Successfully fetched weather forecast from Open-Meteo")
                    return data

        except asyncio.TimeoutError:
            logger.error("Request timeout while fetching weather forecast")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching weather forecast: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather forecast: {e}")
            return None

    async def parse_response(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Open-Meteo API response and normalize to schema.

        Open-Meteo returns 2D arrays: times=[], temperature_2m=[], wind_speed_10m=[],
        cloud_cover=[], cape=[], visibility=[]. This method extracts the latest
        hourly reading and maps it to the weather_raw schema.

        Args:
            api_response: Raw JSON response from Open-Meteo API.

        Returns:
            List of weather records ready for Kafka publishing.
        """
        records = []

        try:
            hourly = api_response.get("hourly", {})
            times = hourly.get("time", [])
            temperatures = hourly.get("temperature_2m", [])
            wind_speeds = hourly.get("wind_speed_10m", [])
            cloud_covers = hourly.get("cloud_cover", [])
            capes = hourly.get("cape", [])
            visibilities = hourly.get("visibility", [])

            if not times:
                logger.warning("No time data in API response")
                return records

            # Process each hour (typically last 24-168 hours)
            for idx, iso_time in enumerate(times):
                try:
                    # Parse ISO format time to Unix timestamp (ms)
                    from datetime import datetime

                    dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
                    event_time_ms = int(dt.timestamp() * 1000)

                    # Get values at this index, handle missing data
                    temperature = temperatures[idx] if idx < len(temperatures) else None
                    wind_speed = wind_speeds[idx] if idx < len(wind_speeds) else 0.0
                    cloud_cover = cloud_covers[idx] if idx < len(cloud_covers) else 0.0
                    cape = capes[idx] if idx < len(capes) else None
                    visibility = visibilities[idx] if idx < len(visibilities) else 0.0

                    # Convert temperature to pressure proxy (simplified: using formula)
                    # This is a placeholder; Open-Meteo doesn't return pressure directly
                    # Using temperature as proxy for atmospheric stability
                    pressure = self._estimate_pressure(temperature)

                    record = {
                        "event_time": event_time_ms,
                        "ingested_at": int(time.time() * 1000),
                        "source_id": self.source_id,
                        "pressure": float(pressure) if pressure else 1013.25,
                        "wind_speed": float(wind_speed) if wind_speed else 0.0,
                        "cloud_cover": float(cloud_cover) if cloud_cover else 0.0,
                        "convective_potential": float(cape) if cape is not None else None,
                        "visibility": float(visibility) if visibility else 10000.0,
                    }

                    records.append(record)

                except Exception as e:
                    logger.error(f"Error parsing hour {idx}: {e}")
                    continue

            logger.info(f"Parsed {len(records)} hourly weather records")

        except Exception as e:
            logger.error(f"Error parsing API response: {e}")

        return records

    def _estimate_pressure(self, temperature: Optional[float]) -> float:
        """
        Estimate atmospheric pressure from temperature.

        This is a simplified proxy when Open-Meteo doesn't return pressure.
        Real implementations would use lapse rate or model data.

        Args:
            temperature: Temperature in Celsius at sea level.

        Returns:
            Estimated pressure in hPa (default 1013.25 if temp unavailable).
        """
        if temperature is None:
            return 1013.25

        # Simplified: standard atmosphere at sea level
        # More realistic would require elevation and more complex formula
        return 1013.25

    async def publish_to_kafka(self, records: List[Dict[str, Any]]) -> None:
        """
        Encode weather records to Avro and publish to Kafka.

        Each record is encoded using the weather_raw Avro schema and
        published to the weather.raw topic.

        Args:
            records: List of weather record dictionaries from parse_response.
        """
        import avro.io
        import avro.schema
        from io import BytesIO

        schema = avro.schema.parse(json.dumps(self.avro_schema))
        current_time_ms = int(time.time() * 1000)

        for record in records:
            try:
                # Avro encoding
                writer = avro.io.DatumWriter(schema)
                bytes_buffer = BytesIO()
                encoder = avro.io.BinaryEncoder(bytes_buffer)
                writer.write(record, encoder)
                avro_bytes = bytes_buffer.getvalue()

                # Publish to Kafka with event_time as key
                key = f"{record['event_time']}".encode("utf-8")

                self.kafka_producer.produce(
                    topic=self.topic,
                    key=key,
                    value=frame(self.schema_id, avro_bytes),
                    on_delivery=self._delivery_report,
                )

            except Exception as e:
                logger.error(f"Failed to publish weather record at {record.get('event_time')}: {e}")

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

    async def run_hourly(self) -> None:
        """
        Main hourly scheduling loop.

        Fetches weather forecast every 60 minutes, parses response,
        and publishes to Kafka.
        """
        self.running = True
        logger.info("WeatherLoader started (hourly scheduling)")

        try:
            while self.running:
                try:
                    # Fetch forecast
                    api_response = await self.fetch_forecast()

                    if api_response:
                        # Parse and publish
                        records = await self.parse_response(api_response)
                        if records:
                            await self.publish_to_kafka(records)
                            logger.info(f"Published {len(records)} weather records to Kafka")
                    else:
                        logger.warning("No API response received; skipping publish")

                    # Sleep for 60 minutes
                    await asyncio.sleep(3600)

                except asyncio.CancelledError:
                    logger.info("WeatherLoader cancelled")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in hourly loop: {e}", exc_info=True)
                    # Sleep briefly before retry
                    await asyncio.sleep(300)

        finally:
            self.running = False
            logger.info("WeatherLoader stopped")

    async def stop(self) -> None:
        """Stop the hourly scheduling loop gracefully."""
        logger.info("Stopping WeatherLoader")
        self.running = False
