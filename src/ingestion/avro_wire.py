"""
Confluent wire-format framing for Avro values published to Kafka.

Each message value is: 1 magic byte (0), a 4-byte big-endian schema ID from the
schema registry, then the Avro binary payload. Consumers use the schema ID to
look up the writer schema, so schemas must be registered before publishing.
"""

import json
import struct
from typing import Any, Dict

from confluent_kafka.schema_registry import Schema, SchemaRegistryClient

MAGIC_BYTE = 0
DEFAULT_COMPATIBILITY = "BACKWARD"


def register_value_schema(
    registry: SchemaRegistryClient,
    topic: str,
    avro_schema: Dict[str, Any],
) -> int:
    """
    Register an Avro schema as the value subject for a topic (TopicNameStrategy).

    Fails at startup if the registry rejects the schema, instead of failing per message.

    Args:
        registry: Schema registry client.
        topic: Kafka topic the schema is published to.
        avro_schema: Parsed Avro schema dictionary.

    Returns:
        Schema ID assigned by the registry.
    """
    subject = f"{topic}-value"
    schema_id = registry.register_schema(subject, Schema(json.dumps(avro_schema), "AVRO"))
    registry.set_compatibility(subject, DEFAULT_COMPATIBILITY)
    return schema_id


def frame(schema_id: int, payload: bytes) -> bytes:
    """
    Prefix an Avro payload with the Confluent wire-format header.

    Args:
        schema_id: Schema ID returned by register_value_schema.
        payload: Avro binary-encoded record.

    Returns:
        Framed message bytes.
    """
    return bytes([MAGIC_BYTE]) + struct.pack(">I", schema_id) + payload
