"""
Kafka end-to-end lag test (WO8): produce-to-consume latency under 5 s.

Requires a running Redpanda/Kafka (KAFKA_BROKERS from .env) and RUN_LOAD_TESTS=1.
Uses a dedicated topic so it never touches alerts.raw.
"""

import json
import time
import uuid

import pytest
from confluent_kafka import Consumer, KafkaException, Producer
from confluent_kafka.admin import AdminClient

from src.config import config as load_config
from tests.conftest import live_only

LAG_BUDGET_S = 5.0
LOAD_TOPIC = "loadtest.lag"
MESSAGES = 20


def _brokers_reachable(brokers: str) -> bool:
    """Return True if the broker answers a metadata request within 2 s."""
    try:
        AdminClient({"bootstrap.servers": brokers}).list_topics(timeout=2)
        return True
    except KafkaException:
        return False


@live_only
def test_kafka_consumer_lag_under_budget() -> None:
    """Every probe message is consumed within 5 s of being produced."""
    brokers = load_config().kafka_brokers
    if not _brokers_reachable(brokers):
        pytest.skip(f"Kafka not reachable at {brokers}")

    run_id = uuid.uuid4().hex
    producer = Producer({"bootstrap.servers": brokers})
    consumer = Consumer(
        {
            "bootstrap.servers": brokers,
            "group.id": f"loadtest-{run_id}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([LOAD_TOPIC])

    produced_at = {}
    for seq in range(MESSAGES):
        payload = json.dumps({"run": run_id, "seq": seq})
        produced_at[seq] = time.time()
        producer.produce(LOAD_TOPIC, value=payload.encode("utf-8"))
    producer.flush(10)

    lags = []
    deadline = time.monotonic() + 60
    try:
        while len(lags) < MESSAGES and time.monotonic() < deadline:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue
            body = json.loads(msg.value())
            if body.get("run") != run_id:
                continue
            lags.append(time.time() - produced_at[body["seq"]])
    finally:
        consumer.close()

    assert len(lags) == MESSAGES, f"consumed {len(lags)}/{MESSAGES} probe messages"
    worst = max(lags)
    assert worst < LAG_BUDGET_S, f"worst Kafka lag {worst:.2f} s exceeds {LAG_BUDGET_S} s"
