"""Auction read operations. Kept separate from bid_service.py because it's
used by both the API layer (auctions.py) and the auction worker
(workers/auction_worker.py), and has no side effects of its own.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.auction import Auction
from services.exceptions import AuctionNotFoundError, AuctionNotLiveError


async def get_auction(db: AsyncSession, auction_id: uuid.UUID) -> Auction:
    result = await db.execute(
        select(Auction).where(Auction.id == auction_id).options(selectinload(Auction.vehicle))
    )
    auction = result.scalar_one_or_none()
    if auction is None:
        raise AuctionNotFoundError(auction_id)
    return auction


async def get_live_auction(db: AsyncSession, auction_id: uuid.UUID) -> Auction:
    """Like get_auction, but also enforces the auction is currently open for bidding."""
    auction = await get_auction(db, auction_id)
    if auction.status != "live":
        raise AuctionNotLiveError(auction_id, auction.status)
    return auction
