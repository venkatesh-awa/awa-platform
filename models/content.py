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

from sqlalchemy import Boolean, ForeignKey, Integer, String, Unicode, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.auction import Auction


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
    title_en: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    title_ar: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    badge_en: Mapped[str | None] = mapped_column(Unicode(50), nullable=True)
    badge_ar: Mapped[str | None] = mapped_column(Unicode(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    auction: Mapped[Auction | None] = relationship()


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
