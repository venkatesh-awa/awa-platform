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
    VehicleListing,
)
from schemas.content import (
    AuctionCategoryRead,
    FeaturedAuctionItemRead,
    FeaturedAuctionTabRead,
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
        icon_class=item.icon_class,
        item_type=item.item_type or "link",
        visibility=item.visibility or "all",
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


async def get_featured_auction_tabs(db: AsyncSession, lang: Lang) -> list[FeaturedAuctionTabRead]:
    result = await db.execute(
        select(FeaturedAuction)
        .where(FeaturedAuction.is_active)
        .order_by(FeaturedAuction.category_sort_order, FeaturedAuction.sort_order)
    )
    tabs_by_key: dict[str, FeaturedAuctionTabRead] = {}
    for row in result.scalars().all():
        category_key = row.category_key or "newly_listed"
        if category_key in tabs_by_key:
            continue
        tabs_by_key[category_key] = FeaturedAuctionTabRead(
            id=row.id,
            category_key=category_key,
            category_label=_pick(row.category_label_en, row.category_label_ar, lang),
            visibility=row.visibility or "all",
            sort_order=row.category_sort_order or 0,
        )
    return list(tabs_by_key.values())


def _featured_auction_item_to_schema(row: FeaturedAuction, lang: Lang) -> FeaturedAuctionItemRead | None:
    vehicle: VehicleListing | None = row.vehicle_listing
    if vehicle is None:
        return None

    auction: Auction | None = row.auction
    # auction_id and vehicle_listing_id are independent nullable links (see
    # models/content.py docstring), so a stale edit could point them at two
    # different vehicles. Only surface live auction data when they agree.
    if auction is not None and auction.vehicle_id != row.vehicle_listing_id:
        auction = None
    return FeaturedAuctionItemRead(
        id=row.id,
        auction_id=row.auction_id,
        vehicle_listing_id=row.vehicle_listing_id,
        title=_pick(vehicle.title_en, vehicle.title_ar, lang),
        image_url=vehicle.image_url,
        badge=_pick(row.badge_en, row.badge_ar, lang) or None,
        category_key=row.category_key or "newly_listed",
        category_label=_pick(row.category_label_en, row.category_label_ar, lang),
        visibility=row.visibility or "all",
        detail_url=vehicle.detail_url,
        lot_number=vehicle.lot_number,
        mileage=vehicle.mileage,
        location=_pick(vehicle.location_en, vehicle.location_ar, lang) or None,
        bid_amount=vehicle.bid_amount,
        countdown_label=vehicle.countdown_label,
        category_sort_order=row.category_sort_order or 0,
        status=auction.status if auction else None,
        starting_price=auction.starting_price if auction else None,
    )


async def get_featured_auction_items(
    db: AsyncSession, lang: Lang, category_key: str
) -> list[FeaturedAuctionItemRead]:
    result = await db.execute(
        select(FeaturedAuction)
        .where(
            FeaturedAuction.is_active,
            FeaturedAuction.category_key == category_key,
            FeaturedAuction.vehicle_listing_id.is_not(None),
        )
        .options(selectinload(FeaturedAuction.auction), selectinload(FeaturedAuction.vehicle_listing))
        .order_by(FeaturedAuction.sort_order, FeaturedAuction.created_at)
    )
    schemas: list[FeaturedAuctionItemRead] = []
    for row in result.scalars().all():
        vehicle: VehicleListing | None = row.vehicle_listing
        if vehicle is None or not vehicle.is_active:
            continue
        item = _featured_auction_item_to_schema(row, lang)
        if item is not None:
            schemas.append(item)
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
