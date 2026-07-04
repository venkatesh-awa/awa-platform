"""Response schemas for the public home-page content API.

Unlike the ORM models (models/content.py), which always carry both `_en` and
`_ar` columns, these schemas expose a single localized field (e.g. `label`,
`name`, `description`) - the caller passes `lang` and services/content_service.py
picks the right column before building these objects. Keeps the frontend free
of any knowledge of the storage convention.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MenuItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    url: str
    icon_class: str | None = None
    item_type: str = "link"
    visibility: str = "all"
    opens_new_tab: bool
    children: list[MenuItemRead] = []


class AuctionCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    icon_url: str | None
    link_url: str


class FeaturedAuctionTabRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_key: str
    category_label: str
    visibility: str = "all"
    sort_order: int = 0


class FeaturedAuctionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    auction_id: uuid.UUID | None
    vehicle_listing_id: uuid.UUID | None = None
    title: str
    image_url: str | None
    badge: str | None
    category_key: str
    category_label: str
    visibility: str = "all"
    detail_url: str | None = None
    lot_number: str | None = None
    mileage: str | None = None
    location: str | None = None
    bid_amount: str | None = None
    countdown_label: str | None = None
    category_sort_order: int = 0
    status: str | None = None
    starting_price: Decimal | None = None


class HowItWorksStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    title: str
    description: str
    icon_url: str | None


class ValueAddedServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    icon_url: str | None
    link_url: str


class FooterLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section: str
    label: str
    url: str


class FooterRead(BaseModel):
    about_text: str
    copyright: str
    support_phone: str | None
    support_email: str | None
    facebook_url: str | None
    instagram_url: str | None
    youtube_url: str | None
    app_store_url: str | None
    google_play_url: str | None
    links: list[FooterLinkRead]


class HomeContentRead(BaseModel):
    auction_categories: list[AuctionCategoryRead]
    featured_auctions: list[FeaturedAuctionTabRead]
    how_it_works: list[HowItWorksStepRead]
    value_added_services: list[ValueAddedServiceRead]
