"""Read operations for the public home-page content (menu, categories,
featured auctions, how-it-works, value-added services, footer).

All content is public/unauthenticated by design - it's marketing chrome, not
user or auction data - so unlike auction_service.py there's no user-scoped
access check here.
"""

from __future__ import annotations

from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.auction import Auction
from models.content import (
    AuctionCategory,
    FeaturedAuction,
    FooterLink,
    FooterSettings,
    HowItWorksStep,
    MenuItem,
    ValueAddedService,
)
from schemas.content import (
    AuctionCategoryRead,
    FeaturedAuctionRead,
    FooterLinkRead,
    FooterRead,
    HowItWorksStepRead,
    MenuItemRead,
    ValueAddedServiceRead,
)

Lang = Literal["en", "ar"]


def _pick(en: str | None, ar: str | None, lang: Lang) -> str:
    """Resolve the localized string for `lang`, falling back to English
    when the Arabic column is unset (e.g. not yet translated)."""
    if lang == "ar" and ar:
        return ar
    return en or ""


def _menu_item_to_schema(item: MenuItem, lang: Lang) -> MenuItemRead:
    return MenuItemRead(
        id=item.id,
        label=_pick(item.label_en, item.label_ar, lang),
        url=item.url,
        opens_new_tab=item.opens_new_tab,
        children=[_menu_item_to_schema(child, lang) for child in item.children if child.is_active],
    )


async def get_menu(db: AsyncSession, lang: Lang) -> list[MenuItemRead]:
    # Nav is two levels deep (top-level items, dropdown children) - eager-load
    # both so _menu_item_to_schema's recursive `.children` access never lazy-loads
    # outside of the request's async context.
    result = await db.execute(
        select(MenuItem)
        .where(MenuItem.parent_id.is_(None), MenuItem.is_active)
        .options(selectinload(MenuItem.children).selectinload(MenuItem.children))
        .order_by(MenuItem.sort_order)
    )
    return [_menu_item_to_schema(item, lang) for item in result.scalars().all()]


async def get_auction_categories(db: AsyncSession, lang: Lang) -> list[AuctionCategoryRead]:
    result = await db.execute(
        select(AuctionCategory)
        .where(AuctionCategory.is_active)
        .order_by(AuctionCategory.sort_order)
    )
    return [
        AuctionCategoryRead(
            id=row.id,
            name=_pick(row.name_en, row.name_ar, lang),
            slug=row.slug,
            icon_url=row.icon_url,
            link_url=row.link_url,
        )
        for row in result.scalars().all()
    ]


async def get_featured_auctions(db: AsyncSession, lang: Lang) -> list[FeaturedAuctionRead]:
    result = await db.execute(
        select(FeaturedAuction)
        .where(FeaturedAuction.is_active)
        .options(selectinload(FeaturedAuction.auction))
        .order_by(FeaturedAuction.sort_order)
    )
    schemas: list[FeaturedAuctionRead] = []
    for row in result.scalars().all():
        auction: Auction | None = row.auction
        schemas.append(
            FeaturedAuctionRead(
                id=row.id,
                auction_id=row.auction_id,
                title=_pick(row.title_en, row.title_ar, lang),
                image_url=row.image_url,
                badge=_pick(row.badge_en, row.badge_ar, lang) or None,
                status=auction.status if auction else None,
                starting_price=auction.starting_price if auction else None,
            )
        )
    return schemas


async def get_how_it_works(db: AsyncSession, lang: Lang) -> list[HowItWorksStepRead]:
    result = await db.execute(
        select(HowItWorksStep)
        .where(HowItWorksStep.is_active)
        .order_by(HowItWorksStep.sort_order)
    )
    return [
        HowItWorksStepRead(
            id=row.id,
            step_number=row.step_number,
            title=_pick(row.title_en, row.title_ar, lang),
            description=_pick(row.description_en, row.description_ar, lang),
            icon_url=row.icon_url,
        )
        for row in result.scalars().all()
    ]


async def get_value_added_services(db: AsyncSession, lang: Lang) -> list[ValueAddedServiceRead]:
    result = await db.execute(
        select(ValueAddedService)
        .where(ValueAddedService.is_active)
        .order_by(ValueAddedService.sort_order)
    )
    return [
        ValueAddedServiceRead(
            id=row.id,
            name=_pick(row.name_en, row.name_ar, lang),
            description=_pick(row.description_en, row.description_ar, lang) or None,
            icon_url=row.icon_url,
            link_url=row.link_url,
        )
        for row in result.scalars().all()
    ]


async def get_footer(db: AsyncSession, lang: Lang) -> FooterRead | None:
    settings_result = await db.execute(select(FooterSettings).limit(1))
    settings = settings_result.scalar_one_or_none()
    if settings is None:
        return None

    links_result = await db.execute(
        select(FooterLink).where(FooterLink.is_active).order_by(FooterLink.sort_order)
    )
    links = [
        FooterLinkRead(
            id=row.id,
            section=row.section,
            label=_pick(row.label_en, row.label_ar, lang),
            url=row.url,
        )
        for row in links_result.scalars().all()
    ]

    return FooterRead(
        about_text=_pick(settings.about_text_en, settings.about_text_ar, lang),
        copyright=_pick(settings.copyright_en, settings.copyright_ar, lang),
        support_phone=settings.support_phone,
        support_email=settings.support_email,
        facebook_url=settings.facebook_url,
        instagram_url=settings.instagram_url,
        youtube_url=settings.youtube_url,
        app_store_url=settings.app_store_url,
        google_play_url=settings.google_play_url,
        links=links,
    )
