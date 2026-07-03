"""Domain exceptions raised by the services layer.

Deliberately framework-agnostic (no FastAPI/HTTPException here) so the same
service functions are reusable from the REST API, the auction worker, and
future callers (CLI tools, other workers) without dragging in a web
framework dependency. Each caller translates these into whatever error
surface makes sense for it - see api/v1/auctions.py for the HTTP mapping.
"""

from __future__ import annotations


class AuctionNotFoundError(Exception):
    def __init__(self, auction_id: object) -> None:
        self.auction_id = auction_id
        super().__init__(f"Auction not found: {auction_id}")


class AuctionNotLiveError(Exception):
    def __init__(self, auction_id: object, status: str) -> None:
        self.auction_id = auction_id
        self.status = status
        super().__init__(f"Auction {auction_id} is not accepting bids (status={status})")


class BidNotEligibleError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class BidPublishError(Exception):
    """Raised when the bid could not be durably published to the event backbone."""


class MalformedBidEvent(Exception):
    """Raised when a message consumed off the Kafka bids topic doesn't parse as
    a valid bid envelope - treated as a poison message by the auction worker,
    not retried indefinitely."""
