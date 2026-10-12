"""
Tests for Confluent wire-format framing and schema registration (src/ingestion/avro_wire.py).
"""

import io
import json
import struct
from unittest.mock import Mock

import avro.io
import avro.schema

from src.ingestion.avro_wire import MAGIC_BYTE, frame, register_value_schema

SCHEMA = {
    "type": "record",
    "name": "probe",
    "namespace": "test",
    "fields": [{"name": "value", "type": "long"}],
}


def test_frame_has_magic_byte_and_big_endian_schema_id() -> None:
    """Framed bytes start with 0x00 followed by the 4-byte big-endian schema ID."""
    framed = frame(258, b"payload")

    assert framed[0] == MAGIC_BYTE == 0
    assert struct.unpack(">I", framed[1:5])[0] == 258
    assert framed[5:] == b"payload"


def test_register_uses_topic_value_subject_and_backward_compatibility() -> None:
    """Schema is registered under '<topic>-value' and compatibility is set to BACKWARD."""
    registry = Mock()
    registry.register_schema.return_value = 7

    schema_id = register_value_schema(registry, "probe.raw", SCHEMA)

    assert schema_id == 7
    subject, schema = registry.register_schema.call_args.args
    assert subject == "probe.raw-value"
    assert schema.schema_type == "AVRO"
    assert json.loads(schema.schema_str) == SCHEMA
    registry.set_compatibility.assert_called_once_with("probe.raw-value", "BACKWARD")


def test_framed_message_round_trips_through_avro() -> None:
    """A consumer that strips the 5-byte header decodes the original record."""
    parsed = avro.schema.parse(json.dumps(SCHEMA))
    buffer = io.BytesIO()
    avro.io.DatumWriter(parsed).write({"value": 1697097600000}, avro.io.BinaryEncoder(buffer))

    framed = frame(3, buffer.getvalue())

    reader = avro.io.DatumReader(parsed)
    decoded = reader.read(avro.io.BinaryDecoder(io.BytesIO(framed[5:])))
    assert decoded == {"value": 1697097600000}
