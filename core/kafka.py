"""Kafka producer/consumer setup (aiokafka).

Design constraints from the architecture document (Section 4.1):
- Bid events are keyed by auction_id so Kafka guarantees ordering per auction.
- Producers must not block the request path on broker unavailability longer
  than a bounded retry window - fail the request cleanly instead of hanging.
- Consumers commit offsets only after the corresponding DB write succeeds,
  so a crashed worker resumes without losing or double-processing a bid.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

_producer: AIOKafkaProducer | None = None


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    reraise=True,
)
async def _start_producer_with_retry(producer: AIOKafkaProducer) -> None:
    await producer.start()


async def init_kafka_producer() -> AIOKafkaProducer:
    global _producer
    settings = get_settings()
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        acks="all",  # wait for all in-sync replicas - durability over raw throughput
        enable_idempotence=True,  # dedupes retried sends, avoids double-publish
        request_timeout_ms=10_000,
        linger_ms=5,
    )
    await _start_producer_with_retry(_producer)
    logger.info("kafka_producer_started")
    return _producer


async def dispose_kafka_producer() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("kafka_producer_stopped")


def get_kafka_producer() -> AIOKafkaProducer:
    if _producer is None:
        raise RuntimeError("Kafka producer not initialized. Call init_kafka_producer() at startup.")
    return _producer


async def publish_event(topic: str, key: str, value: bytes) -> None:
    """Publish a single event. Raises on failure - callers decide how to surface that to the client."""
    producer = get_kafka_producer()
    await producer.send_and_wait(topic, key=key.encode("utf-8"), value=value)


def make_consumer(topics: list[str], group_id: str | None = None) -> AIOKafkaConsumer:
    """Factory for a consumer bound to specific topics and consumer group.

    enable_auto_commit is deliberately False: workers commit offsets manually
    only after the corresponding database write succeeds (see auction_worker.py).
    """
    settings = get_settings()
    return AIOKafkaConsumer(
        *topics,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=group_id or settings.kafka_consumer_group,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        max_poll_records=50,
    )


async def consume_with_backoff(consumer: AIOKafkaConsumer) -> AsyncGenerator[object, None]:
    """Yield messages, restarting the consumer loop with backoff on transient errors
    instead of crashing the worker process outright."""
    await consumer.start()
    try:
        async for message in consumer:
            yield message
    finally:
        await consumer.stop()
