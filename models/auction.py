"""Core ORM models. PostgreSQL is the source of truth (architecture doc Section 8) -
Redis and any in-memory state must always be reconstructible from these tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Auction(Base):
    __tablename__ = "auctions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    starting_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reserve_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bids: Mapped[list["Bid"]] = relationship(back_populates="auction", order_by="Bid.created_at")

    __table_args__ = (
        CheckConstraint("starting_price >= 0", name="ck_auction_starting_price_nonneg"),
        CheckConstraint("ends_at > starts_at", name="ck_auction_ends_after_starts"),
        Index("ix_auctions_status_ends_at", "status", "ends_at"),
    )


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auctions.id", ondelete="CASCADE"), nullable=False
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # kafka_offset ties a bid row back to the exact log position that produced it,
    # which is what makes worker restarts idempotent (see auction_worker.py).
    kafka_partition: Mapped[int | None] = mapped_column(nullable=True)
    kafka_offset: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    auction: Mapped[Auction] = relationship(back_populates="bids")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_bid_amount_positive"),
        CheckConstraint(
            "status in ('pending','accepted','rejected')", name="ck_bid_status_valid"
        ),
        Index("ix_bids_auction_amount", "auction_id", "amount"),
        # Prevents double-processing the same Kafka message twice into two DB rows.
        Index(
            "uq_bids_kafka_position",
            "kafka_partition",
            "kafka_offset",
            unique=True,
            postgresql_where="kafka_offset IS NOT NULL",
        ),
    )
