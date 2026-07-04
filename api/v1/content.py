"""Public home-page content endpoints - menu, footer, and the home page's
own sections (categories, featured auctions, how it works, value-added
services). Unauthenticated by design: this is marketing chrome, served to
every visitor before login.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db_session
from schemas.content import FeaturedAuctionItemRead, FooterRead, HomeContentRead, MenuItemRead
from services import content_service

router = APIRouter(prefix="/content", tags=["content"])

LangQuery = Literal["en", "ar"]


@router.get("/menu", response_model=list[MenuItemRead])
async def get_menu(
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> list[MenuItemRead]:
    return await content_service.get_menu(db, lang)


@router.get("/footer", response_model=FooterRead)
async def get_footer(
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> FooterRead:
    footer = await content_service.get_footer(db, lang)
    if footer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Footer content not configured")
    return footer


@router.get("/home", response_model=HomeContentRead)
async def get_home(
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> HomeContentRead:
    return HomeContentRead(
        auction_categories=await content_service.get_auction_categories(db, lang),
        featured_auctions=await content_service.get_featured_auction_tabs(db, lang),
        how_it_works=await content_service.get_how_it_works(db, lang),
        value_added_services=await content_service.get_value_added_services(db, lang),
    )


@router.get("/featured-auctions/{category_key}/items", response_model=list[FeaturedAuctionItemRead])
async def get_featured_auction_items(
    category_key: str,
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> list[FeaturedAuctionItemRead]:
    return await content_service.get_featured_auction_items(db, lang, category_key)
