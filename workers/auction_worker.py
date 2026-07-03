"""Auction worker: the Kafka consumer loop for the critical path in the
architecture document (Section 5). All decision logic lives in
services/bid_service.decide_bid() - this module is deliberately thin: it
owns the consumer lifecycle, offset commit timing, and error handling
around a poison-message vs. transient-failure distinction.

Run as a SEPARATE process from the API (see docker-compose.yml / k8s
manifests - `python -m workers.auction_worker`), never inside the
request/response cycle. Kafka's consumer-group protocol guarantees exactly
one instance of this worker owns any given partition at a time, which is
what makes bid processing for a single auction strictly serial with zero
extra locking required.

Offset commit happens only AFTER the Postgres write in decide_bid()
succeeds, so a crash between "consumed" and "committed" replays the message
on restart rather than silently dropping a bid - the unique index on
(kafka_partition, kafka_offset) in models/auction.py makes that replay
idempotent.
"""

from __future__ import annotations

import asyncio
import signal

from core.config import get_settings
from core.database import dispose_engine, init_engine
from core.kafka import consume_with_backoff, dispose_kafka_producer, init_kafka_producer, make_consumer
from core.logging import configure_logging, get_logger
from core.redis import dispose_redis, init_redis
from services.bid_service import decide_bid, parse_bid_envelope
from services.exceptions import MalformedBidEvent

logger = get_logger(__name__)

_shutdown_event = asyncio.Event()


async def run_worker() -> None:
    configure_logging()
    settings = get_settings()

    init_engine()
    init_redis()
    await init_kafka_producer()

    consumer = make_consumer([settings.kafka_topic_bids])
    logger.info("auction_worker_starting", topic=settings.kafka_topic_bids)

    try:
        async for message in consume_with_backoff(consumer):
            if _shutdown_event.is_set():
                break
            try:
                envelope = parse_bid_envelope(message.value)
                await decide_bid(envelope, message.partition, message.offset)
            except MalformedBidEvent:
                logger.exception(
                    "malformed_bid_event_skipped",
                    partition=message.partition,
                    offset=message.offset,
                )
                # Deliberately fall through to commit: a poison message must not
                # block the partition forever. Route it to a dead-letter topic
                # in production instead of silently skipping.
            except Exception:
                logger.exception(
                    "bid_processing_failed_will_retry",
                    partition=message.partition,
                    offset=message.offset,
                )
                # Do NOT commit - this message will be redelivered after restart.
                continue

            await consumer.commit()
    finally:
        await consumer.stop()
        await dispose_kafka_producer()
        await dispose_redis()
        await dispose_engine()
        logger.info("auction_worker_stopped")


def _handle_shutdown_signal(*_args: object) -> None:
    _shutdown_event.set()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_shutdown_signal)
    loop.run_until_complete(run_worker())
