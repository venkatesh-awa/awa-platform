"""Bid business logic, split into two halves that mirror the critical path
in the architecture document (Section 5):

- submit_bid(): steps 1-2, called from the API layer. Fast pre-validation,
  then publish to Kafka. Never decides accept/reject itself.
- decide_bid(): steps 3-5, called from the auction worker. The single
  source of truth for whether a bid wins - owns the SQL Server write, the
  Redis cache update, and the result event publication.

Kept framework-agnostic (raises services.exceptions, not HTTPException) so
both callers - one HTTP, one a Kafka consumer loop - can use it directly.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import session_scope
from core.kafka import publish_event
from core.logging import get_logger
from core.redis import publish_bid_update, try_accept_bid
from core.security import CurrentUser
from models.auction import Auction, Bid
from schemas.bid import BidAccepted, BidResult
from services.auction_service import get_live_auction
from services.exceptions import BidNotEligibleError, BidPublishError, MalformedBidEvent

logger = get_logger(__name__)

REQUIRED_BID_ROLES = ("Buyer", "AuctionsHead")
_REQUIRED_ENVELOPE_FIELDS = {"bid_id", "auction_id", "bidder_id", "amount", "submitted_at"}
_ENVELOPE_UUID_FIELDS = ("bid_id", "auction_id", "bidder_id")


def parse_bid_envelope(raw_value: bytes) -> dict:
    """Validate a raw Kafka message as a well-formed bid envelope. Raises
    MalformedBidEvent for anything that can never succeed (bad JSON, missing
    fields, invalid UUIDs, non-numeric amount) so the worker treats it as a
    poison message to skip, rather than retrying it forever.
    """
    try:
        data = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise MalformedBidEvent(f"invalid JSON: {exc}") from exc

    missing = _REQUIRED_ENVELOPE_FIELDS - data.keys()
    if missing:
        raise MalformedBidEvent(f"missing fields: {missing}")

    try:
        Decimal(data["amount"])
    except InvalidOperation as exc:
        raise MalformedBidEvent(f"invalid amount: {data['amount']!r}") from exc

    for field in _ENVELOPE_UUID_FIELDS:
        try:
            uuid.UUID(str(data[field]))
        except ValueError as exc:
            raise MalformedBidEvent(f"invalid UUID in field {field!r}: {data[field]!r}") from exc

    return data


def validate_bid_eligibility(user: CurrentUser, amount: Decimal) -> None:  # noqa: ARG001
    """Fast pre-check before publishing to Kafka. Deliberately conservative:
    this is a UX-speed gate, not the source of truth for eligibility - the
    auction worker re-validates against committed state in decide_bid().
    Wire this up to the real deposit/buying-limit service in a later sprint.
    """
    if not any(user.has_role(role) for role in REQUIRED_BID_ROLES):
        raise BidNotEligibleError(
            f"Only {' or '.join(REQUIRED_BID_ROLES)} roles may place bids (BRD R088)"
        )


async def submit_bid(db: AsyncSession, auction_id: uuid.UUID, user: CurrentUser, amount: Decimal) -> BidAccepted:
    """Validate and publish a bid. Returns immediately once the event is
    durably on the Kafka log - the actual accept/reject decision arrives
    later via WebSocket, produced by decide_bid() below."""
    settings = get_settings()

    await get_live_auction(db, auction_id)
    validate_bid_eligibility(user, amount)

    bid_id = uuid.uuid4()
    submitted_at = datetime.now(UTC)

    envelope = {
        "bid_id": str(bid_id),
        "auction_id": str(auction_id),
        "bidder_id": user.subject,
        "amount": str(amount),
        "submitted_at": submitted_at.isoformat(),
    }

    try:
        await publish_event(
            topic=settings.kafka_topic_bids,
            key=str(auction_id),  # partition key -> per-auction ordering guarantee
            value=json.dumps(envelope).encode("utf-8"),
        )
    except Exception as exc:
        logger.exception("bid_publish_failed", auction_id=str(auction_id), bid_id=str(bid_id))
        raise BidPublishError from exc

    logger.info("bid_submitted", auction_id=str(auction_id), bid_id=str(bid_id), bidder_id=user.subject)

    return BidAccepted(bid_id=bid_id, auction_id=auction_id, status="received", submitted_at=submitted_at)


async def decide_bid(envelope: dict, partition: int, offset: int) -> BidResult | None:
    """The correctness-critical decision: is this bid the new highest bid?

    Called exclusively from the auction worker, which guarantees exactly one
    call is ever in flight per auction (Kafka single-writer-per-partition).
    Returns None if this exact Kafka message was already processed in a
    prior run (safe no-op on offset replay after a crash).
    """
    auction_id = uuid.UUID(envelope["auction_id"])
    bid_id = uuid.UUID(envelope["bid_id"])
    bidder_id = uuid.UUID(envelope["bidder_id"])
    amount = Decimal(envelope["amount"])
    decided_at = datetime.now(UTC)

    async with session_scope() as db:
        result = await db.execute(select(Auction).where(Auction.id == auction_id))
        auction = result.scalar_one_or_none()

        if auction is None or auction.status != "live":
            status_, reason = "rejected", "auction_not_live"
        else:
            highest = await db.execute(
                select(Bid.amount)
                .where(Bid.auction_id == auction_id, Bid.status == "accepted")
                .order_by(Bid.amount.desc())
                .limit(1)
            )
            current_high = highest.scalar_one_or_none() or auction.starting_price
            status_, reason = ("accepted", None) if amount > current_high else ("rejected", "not_highest")

        bid_row = Bid(
            id=bid_id,
            auction_id=auction_id,
            bidder_id=bidder_id,
            amount=amount,
            status=status_,
            kafka_partition=partition,
            kafka_offset=offset,
        )
        try:
            db.add(bid_row)
            await db.flush()  # surfaces the unique-index violation before we commit
        except IntegrityError:
            logger.info("bid_already_processed", bid_id=str(bid_id), partition=partition, offset=offset)
            return None

    # DB commit succeeded (session_scope commits on clean exit) - now update the
    # fast-read cache and fan out to connected clients. Neither of these steps
    # can make an already-committed decision wrong; they only affect latency.
    if status_ == "accepted":
        await try_accept_bid(str(auction_id), str(amount), str(bidder_id), decided_at.isoformat())

    result_event = BidResult(
        bid_id=bid_id,
        auction_id=auction_id,
        bidder_id=bidder_id,
        amount=amount,
        status=status_,
        reason=reason,
        decided_at=decided_at,
    )
    await publish_bid_update(str(auction_id), result_event.model_dump_json())

    settings = get_settings()
    await publish_event(
        topic=settings.kafka_topic_bid_results,
        key=str(auction_id),
        value=result_event.model_dump_json().encode("utf-8"),
    )

    logger.info("bid_processed", bid_id=str(bid_id), auction_id=str(auction_id), status=status_)
    return result_event
