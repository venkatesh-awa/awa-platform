"""Request/response schemas. Kept separate from ORM models (app/models) so the
wire format can evolve independently of the database schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BidCreate(BaseModel):
    amount: Decimal = Field(gt=0, description="Bid amount, must be strictly positive")

    @field_validator("amount")
    @classmethod
    def reasonable_precision(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -2:
            raise ValueError("amount supports at most 2 decimal places")
        return v


class BidAccepted(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bid_id: uuid.UUID
    auction_id: uuid.UUID
    status: str = "received"
    submitted_at: datetime


class BidResult(BaseModel):
    """Published on the Kafka bid-results topic and pushed to clients over the
    WebSocket gateway once the auction worker has made a final decision."""

    bid_id: uuid.UUID
    auction_id: uuid.UUID
    bidder_id: uuid.UUID
    amount: Decimal
    status: str  # accepted | rejected
    reason: str | None = None
    decided_at: datetime


class AuctionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    status: str
    starting_price: Decimal
    reserve_price: Decimal | None
    starts_at: datetime
    ends_at: datetime
