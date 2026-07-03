"""Redis client: connection pooling, health checks, pub/sub helpers, and the
atomic bid-arbitration script referenced in the architecture document
(Section 5.2). Redis here is a derived cache, never the source of truth -
every value it holds must be reconstructible from SQL Server.
"""

from __future__ import annotations

from redis.asyncio import ConnectionPool, Redis

from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

_pool: ConnectionPool | None = None
_client: Redis | None = None

# KEYS[1] = auction:{auction_id}:highest_bid
# ARGV[1] = new_bid_amount, ARGV[2] = bidder_id, ARGV[3] = timestamp (iso8601)
# Atomic compare-and-set: only accepts a bid strictly higher than the current one.
BID_ARBITRATION_SCRIPT = """
local current = tonumber(redis.call('HGET', KEYS[1], 'amount') or '0')
if tonumber(ARGV[1]) > current then
  redis.call('HSET', KEYS[1], 'amount', ARGV[1], 'bidder_id', ARGV[2], 'ts', ARGV[3])
  return 1
else
  return 0
end
"""


def init_redis() -> Redis:
    global _pool, _client
    settings = get_settings()
    _pool = ConnectionPool.from_url(
        str(settings.redis_url),
        max_connections=50,
        decode_responses=True,
    )
    _client = Redis(connection_pool=_pool)
    logger.info("redis_client_initialized")
    return _client


async def dispose_redis() -> None:
    global _client, _pool
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
    logger.info("redis_client_disposed")


def get_redis() -> Redis:
    if _client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() at startup.")
    return _client


async def check_redis_health() -> bool:
    try:
        client = get_redis()
        return bool(await client.ping())
    except Exception:
        logger.exception("redis_health_check_failed")
        return False


async def try_accept_bid(auction_id: str, amount: str, bidder_id: str, ts: str) -> bool:
    """Atomically compare-and-set the highest bid for an auction in the Redis cache.

    This does NOT decide correctness by itself - the auction worker (see
    app/workers/auction_worker.py) is the single-writer-per-partition owner
    of the decision; this call keeps the fast-read cache consistent with it.
    """
    client = get_redis()
    result = await client.eval(
        BID_ARBITRATION_SCRIPT,
        1,
        f"auction:{auction_id}:highest_bid",
        amount,
        bidder_id,
        ts,
    )
    return bool(result)


async def publish_bid_update(auction_id: str, payload: str) -> None:
    """Fan-out an accepted bid to every WebSocket gateway node subscribed to this auction."""
    client = get_redis()
    await client.publish(f"auction:{auction_id}:updates", payload)
