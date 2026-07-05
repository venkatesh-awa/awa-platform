"""Home page content models - menu, footer, and marketing sections.

All translatable fields use paired `_en`/`_ar` columns rather than a generic
translations table: only two locales are required (architecture doc Section 8
scope), and this matches the flat-column style already used across the app.
Localization to a single display string happens in services/content_service.py,
not here - these models always carry both languages.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Unicode, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.auction import Auction

if TYPE_CHECKING:
    from models.sub_seller import SubSeller
    from models.user import User
    from models.vehicle_intake import (
        BiddingModel,
        FuelType,
        VehicleBranch,
        VehicleColor,
        VehicleKeyOption,
        VehicleMake,
        VehicleModel,
    )


class VehicleListing(Base):
    """A vehicle known to the platform - spans both publicly published
    auction listings (the original use of this table) and seller intake
    submissions from the "Add a New Car" form (`status` starts at
    "submitted", `is_active` False, until reviewed and published). One table
    rather than two so a submission becomes a listing in place instead of
    needing a separate copy/migration step once approved.
    """

    __tablename__ = "vehicle_listings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable: existing/admin-curated listings (see 0006_vehicle_listings
    # backfill) have no seller of record. SET NULL rather than CASCADE so
    # deleting a seller's account doesn't also delete their vehicle listings
    # and any auctions/bids built on top of them. Doubles as the "Client"
    # on a seller intake submission - there's no distinct concept of a
    # submission's client vs. a listing's seller.
    seller_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title_en: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    title_ar: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    detail_url: Mapped[str] = mapped_column(String(500), nullable=False)
    lot_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mileage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location_en: Mapped[str | None] = mapped_column(Unicode(100), nullable=True)
    location_ar: Mapped[str | None] = mapped_column(Unicode(100), nullable=True)
    bid_amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    countdown_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Seller intake fields ("Add a New Car" form) - nullable since
    # pre-existing/admin-curated listings never went through that form. ---
    chassis_number: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    make_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("vehicle_makes.id", ondelete="NO ACTION"), nullable=True
    )
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("vehicle_models.id", ondelete="NO ACTION"), nullable=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("vehicle_branches.id", ondelete="NO ACTION"), nullable=True
    )
    color_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("vehicle_colors.id", ondelete="NO ACTION"), nullable=True
    )
    keys_option_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("vehicle_key_options.id", ondelete="NO ACTION"), nullable=True
    )
    fuel_type_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fuel_types.id", ondelete="NO ACTION"), nullable=True
    )
    bidding_model_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("bidding_models.id", ondelete="SET NULL"), nullable=True
    )
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_selling_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    minimum_selling_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    previous_number_plate: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # A named contact under the client submitting on their behalf - distinct
    # from `seller_id` (the client) and `created_by_id` (the admin operator).
    # References sub_sellers, not users: a sub-seller isn't its own account.
    # NO ACTION (not SET NULL): sub_sellers.seller_id cascades into users, and
    # SQL Server rejects a second cascade path into users via this column.
    sub_seller_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sub_sellers.id", ondelete="NO ACTION"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )
    mulkhiya_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Intake review state ("submitted", "approved", "rejected", ...),
    # distinct from `is_active` (whether it's shown as a public listing).
    # Pre-existing rows are backfilled to "published" (see migration).
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    auctions: Mapped[list[Auction]] = relationship(back_populates="vehicle")
    seller: Mapped[User | None] = relationship(back_populates="vehicle_listings", foreign_keys=[seller_id])
    sub_seller: Mapped[SubSeller | None] = relationship()
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    make: Mapped[VehicleMake | None] = relationship()
    model: Mapped[VehicleModel | None] = relationship()
    branch: Mapped[VehicleBranch | None] = relationship()
    color: Mapped[VehicleColor | None] = relationship()
    keys_option: Mapped[VehicleKeyOption | None] = relationship()
    fuel_type: Mapped[FuelType | None] = relationship()
    bidding_model: Mapped[BiddingModel | None] = relationship()


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # NO ACTION (not CASCADE): SQL Server rejects a self-referencing FK with a
    # cascade path since a delete could cycle back to the same table.
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("menu_items.id", ondelete="NO ACTION"), nullable=True
    )
    label_en: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    label_ar: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    icon_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False, default="link")
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="all")
    opens_new_tab: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    children: Mapped[list[MenuItem]] = relationship(
        back_populates="parent", order_by="MenuItem.sort_order"
    )
    parent: Mapped[MenuItem | None] = relationship(back_populates="children", remote_side=[id])


class AuctionCategory(Base):
    __tablename__ = "auction_categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_en: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    name_ar: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    link_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class FeaturedAuction(Base):
    """Editorial "featured" placements shown on the home page. Not every
    featured item corresponds to a live auction row (curated/upcoming
    listings need to be promotable before bidding opens), so `auction_id` is
    a nullable link rather than a strict FK requirement - when set, the
    service joins in live price/status from `auctions`.
    """

    __tablename__ = "featured_auctions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("auctions.id", ondelete="SET NULL"), nullable=True
    )
    vehicle_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("vehicle_listings.id", ondelete="SET NULL"), nullable=True
    )
    badge_en: Mapped[str | None] = mapped_column(Unicode(50), nullable=True)
    badge_ar: Mapped[str | None] = mapped_column(Unicode(50), nullable=True)
    category_key: Mapped[str] = mapped_column(String(80), nullable=False, default="newly_listed")
    category_label_en: Mapped[str] = mapped_column(Unicode(100), nullable=False, default="Newly Listed Vehicles")
    category_label_ar: Mapped[str] = mapped_column(Unicode(100), nullable=False, default="مركبات مدرجة حديثًا")
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="all")
    category_sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    auction: Mapped[Auction | None] = relationship()
    vehicle_listing: Mapped[VehicleListing | None] = relationship()


class HowItWorksStep(Base):
    __tablename__ = "how_it_works_steps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_en: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    title_ar: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    description_en: Mapped[str] = mapped_column(Unicode(500), nullable=False)
    description_ar: Mapped[str] = mapped_column(Unicode(500), nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class ValueAddedService(Base):
    __tablename__ = "value_added_services"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_en: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    name_ar: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    description_en: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    description_ar: Mapped[str | None] = mapped_column(Unicode(500), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    link_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class FooterSettings(Base):
    """Singleton row (a single fixed id) holding footer copy that isn't a list of links."""

    __tablename__ = "footer_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    about_text_en: Mapped[str] = mapped_column(Unicode(1000), nullable=False)
    about_text_ar: Mapped[str] = mapped_column(Unicode(1000), nullable=False)
    copyright_en: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    copyright_ar: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    support_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    app_store_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_play_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class FooterLink(Base):
    __tablename__ = "footer_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section: Mapped[str] = mapped_column(String(50), nullable=False, default="quick_links")
    label_en: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    label_ar: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
