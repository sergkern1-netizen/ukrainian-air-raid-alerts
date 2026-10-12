"""
Tests for BatchLoader.publish_to_kafka: Confluent wire format via confluent-kafka.
"""

import struct
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.ingestion.batch_loaders import BatchLoader

SCHEMA = {
    "type": "record",
    "name": "batch_probe",
    "namespace": "test",
    "fields": [
        {"name": "event_time", "type": "long"},
        {"name": "value", "type": "double"},
        {"name": "label", "type": "string"},
    ],
}


class _Probe(BatchLoader):
    """Minimal concrete loader for exercising the base-class publish path."""

    def load(self) -> pd.DataFrame:
        return pd.DataFrame()

    def validate_schema(self, df: pd.DataFrame) -> bool:
        return True

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


@pytest.fixture
def loader(tmp_path) -> _Probe:
    return _Probe(kafka_brokers="localhost:9092", output_dir=str(tmp_path))


@pytest.fixture
def registry() -> Mock:
    registry = Mock()
    registry.register_schema.return_value = 42
    return registry


def _frame() -> pd.DataFrame:
    # int64 and float64 columns: pandas yields NumPy scalars, not Python ints/floats
    return pd.DataFrame(
        {"event_time": [1697097600000, 1697101200000], "value": [1.5, 2.0], "label": ["a", "b"]}
    )


def test_publish_frames_each_record_with_registered_schema_id(loader, registry) -> None:
    producer = Mock()
    with patch("src.ingestion.batch_loaders.Producer", return_value=producer):
        count = loader.publish_to_kafka(_frame(), "probe.raw", SCHEMA, registry)

    assert count == 2
    registry.register_schema.assert_called_once()
    assert registry.register_schema.call_args.args[0] == "probe.raw-value"
    assert producer.produce.call_count == 2
    for call in producer.produce.call_args_list:
        value = call.kwargs["value"]
        assert value[0] == 0
        assert struct.unpack(">I", value[1:5])[0] == 42
    producer.flush.assert_called_once()


def test_numpy_scalars_encode_without_error(loader, registry) -> None:
    """Regression guard: NumPy int64/float64 values must satisfy Avro long/double."""
    producer = Mock()
    with patch("src.ingestion.batch_loaders.Producer", return_value=producer):
        assert loader.publish_to_kafka(_frame(), "probe.raw", SCHEMA, registry) == 2


def test_no_brokers_skips_without_touching_registry(tmp_path, registry) -> None:
    loader = _Probe(kafka_brokers=None, output_dir=str(tmp_path))
    with patch("src.ingestion.batch_loaders.Producer") as producer_cls:
        assert loader.publish_to_kafka(_frame(), "probe.raw", SCHEMA, registry) == 0
    producer_cls.assert_not_called()
    registry.register_schema.assert_not_called()


def test_brokers_without_registry_fails_fast(loader) -> None:
    with pytest.raises(ValueError, match="schema_registry is required"):
        loader.publish_to_kafka(_frame(), "probe.raw", SCHEMA)
