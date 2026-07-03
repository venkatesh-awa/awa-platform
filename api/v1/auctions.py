"""Auction and bid REST endpoints - a thin controller layer.

All business logic lives in services/auction_service.py and
services/bid_service.py; this module's only job is HTTP concerns:
routing, request/response schemas, and translating domain exceptions
(services/exceptions.py) into HTTP status codes.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import CurrentUser, get_current_user, get_db_session
from models.auction import Auction
from schemas.bid import AuctionRead, BidAccepted, BidCreate
from services import auction_service, bid_service
from services.exceptions import (
    AuctionNotFoundError,
    AuctionNotLiveError,
    BidNotEligibleError,
    BidPublishError,
)

router = APIRouter(prefix="/auctions", tags=["auctions"])


@router.get("/{auction_id}", response_model=AuctionRead)
async def get_auction(auction_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> Auction:
    try:
        return await auction_service.get_auction(db, auction_id)
    except AuctionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auction not found") from exc


@router.post(
    "/{auction_id}/bids",
    response_model=BidAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a bid (async - final accept/reject arrives via WebSocket)",
)
async def submit_bid(
    auction_id: uuid.UUID,
    payload: BidCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> BidAccepted:
    try:
        return await bid_service.submit_bid(db, auction_id, user, payload.amount)
    except AuctionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auction not found") from exc
    except AuctionNotLiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Auction is not accepting bids (status={exc.status})",
        ) from exc
    except BidNotEligibleError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.reason) from exc
    except BidPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to submit bid right now, please retry",
        ) from exc
