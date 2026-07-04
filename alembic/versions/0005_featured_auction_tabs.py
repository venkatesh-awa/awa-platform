"""featured auction tabs and card metadata

Revision ID: 0005_featured_auction_tabs
Revises: 0004_menu_item_metadata
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_featured_auction_tabs"
down_revision: str | None = "0004_menu_item_metadata"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

VEHICLE_IMAGE_URL = (
    "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?"
    "auto=format&fit=crop&w=640&q=85"
)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def upgrade() -> None:
    op.add_column(
        "featured_auctions",
        sa.Column("category_key", sa.String(length=80), nullable=False, server_default="newly_listed"),
    )
    op.add_column(
        "featured_auctions",
        sa.Column(
            "category_label_en",
            sa.Unicode(length=100),
            nullable=False,
            server_default="Newly Listed Vehicles",
        ),
    )
    op.add_column(
        "featured_auctions",
        sa.Column(
            "category_label_ar",
            sa.Unicode(length=100),
            nullable=False,
            server_default="مركبات مدرجة حديثًا",
        ),
    )
    op.add_column(
        "featured_auctions",
        sa.Column("visibility", sa.String(length=30), nullable=False, server_default="all"),
    )
    op.add_column("featured_auctions", sa.Column("detail_url", sa.String(length=500), nullable=True))
    op.add_column("featured_auctions", sa.Column("lot_number", sa.String(length=50), nullable=True))
    op.add_column("featured_auctions", sa.Column("mileage", sa.String(length=50), nullable=True))
    op.add_column("featured_auctions", sa.Column("location_en", sa.Unicode(length=100), nullable=True))
    op.add_column("featured_auctions", sa.Column("location_ar", sa.Unicode(length=100), nullable=True))
    op.add_column("featured_auctions", sa.Column("bid_amount", sa.String(length=50), nullable=True))
    op.add_column("featured_auctions", sa.Column("countdown_label", sa.String(length=50), nullable=True))
    op.add_column(
        "featured_auctions",
        sa.Column("category_sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    _update_existing_public_rows()
    _insert_authenticated_rows()

    op.alter_column("featured_auctions", "category_key", server_default=None)
    op.alter_column("featured_auctions", "category_label_en", server_default=None)
    op.alter_column("featured_auctions", "category_label_ar", server_default=None)
    op.alter_column("featured_auctions", "visibility", server_default=None)
    op.alter_column("featured_auctions", "category_sort_order", server_default=None)


def _update_existing_public_rows() -> None:
    public_rows = [
        {
            "match_badge": "New",
            "category_key": "newly_listed",
            "category_label_en": "Newly Listed Vehicles",
            "category_label_ar": "مركبات مدرجة حديثًا",
            "title_en": "Toyota Land Cruiser 2025",
            "title_ar": "تويوتا لاند كروزر 2025",
            "category_sort_order": 5,
            "sort_order": 1,
        },
        {
            "match_badge": "Ending Soon",
            "category_key": "ending_soon",
            "category_label_en": "Ending Soon",
            "category_label_ar": "ينتهي قريبًا",
            "title_en": "Nissan Patrol Platinum 2024",
            "title_ar": "نيسان باترول بلاتينيوم 2024",
            "category_sort_order": 2,
            "sort_order": 1,
        },
        {
            "match_badge": "Hot",
            "category_key": "hot_items",
            "category_label_en": "Hot Items",
            "category_label_ar": "عناصر رائجة",
            "title_en": "Mercedes-Benz GLE 2023",
            "title_ar": "مرسيدس بنز GLE 2023",
            "category_sort_order": 6,
            "sort_order": 1,
        },
    ]

    for row in public_rows:
        op.execute(
            sa.text(
                """
                UPDATE featured_auctions
                SET category_key = :category_key,
                    category_label_en = :category_label_en,
                    category_label_ar = :category_label_ar,
                    title_en = :title_en,
                    title_ar = :title_ar,
                    visibility = 'all',
                    image_url = COALESCE(image_url, :image_url),
                    detail_url = COALESCE(detail_url, '/seller-buyer/vehicle-details/102684'),
                    lot_number = COALESCE(lot_number, '102684'),
                    mileage = COALESCE(mileage, '100002 KM'),
                    location_en = COALESCE(location_en, 'Abu Dhabi'),
                    location_ar = COALESCE(location_ar, 'أبوظبي'),
                    bid_amount = COALESCE(bid_amount, 'AED 5,500'),
                    countdown_label = COALESCE(countdown_label, '3D: 2H: 48M: 46S'),
                    category_sort_order = :category_sort_order,
                    sort_order = :sort_order
                WHERE badge_en = :match_badge
                """
            ).bindparams(**row, image_url=VEHICLE_IMAGE_URL)
        )


def _insert_authenticated_rows() -> None:
    featured_auctions = sa.table(
        "featured_auctions",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("auction_id", sa.Uuid(as_uuid=True)),
        sa.column("title_en", sa.Unicode(length=200)),
        sa.column("title_ar", sa.Unicode(length=200)),
        sa.column("image_url", sa.String(length=500)),
        sa.column("badge_en", sa.Unicode(length=50)),
        sa.column("badge_ar", sa.Unicode(length=50)),
        sa.column("category_key", sa.String(length=80)),
        sa.column("category_label_en", sa.Unicode(length=100)),
        sa.column("category_label_ar", sa.Unicode(length=100)),
        sa.column("visibility", sa.String(length=30)),
        sa.column("detail_url", sa.String(length=500)),
        sa.column("lot_number", sa.String(length=50)),
        sa.column("mileage", sa.String(length=50)),
        sa.column("location_en", sa.Unicode(length=100)),
        sa.column("location_ar", sa.Unicode(length=100)),
        sa.column("bid_amount", sa.String(length=50)),
        sa.column("countdown_label", sa.String(length=50)),
        sa.column("category_sort_order", sa.Integer()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    base = {
        "auction_id": None,
        "image_url": VEHICLE_IMAGE_URL,
        "detail_url": "/seller-buyer/vehicle-details/102684",
        "lot_number": "102684",
        "mileage": "100002 KM",
        "location_en": "Abu Dhabi",
        "location_ar": "أبوظبي",
        "bid_amount": "AED 5,500",
        "countdown_label": "3D: 2H: 48M: 46S",
        "visibility": "authenticated",
        "sort_order": 1,
        "is_active": True,
    }
    op.bulk_insert(
        featured_auctions,
        [
            {
                **base,
                "id": _uuid(),
                "title_en": "Toyota Land Cruiser 2025",
                "title_ar": "تويوتا لاند كروزر 2025",
                "badge_en": "Recommended",
                "badge_ar": "موصى به",
                "category_key": "recommended",
                "category_label_en": "Recommended",
                "category_label_ar": "موصى به",
                "category_sort_order": 1,
            },
            {
                **base,
                "id": _uuid(),
                "title_en": "Recently Viewed Vehicle",
                "title_ar": "مركبة تمت مشاهدتها مؤخرًا",
                "badge_en": "Recently Viewed",
                "badge_ar": "شوهد مؤخرًا",
                "category_key": "recently_viewed",
                "category_label_en": "Recently Viewed",
                "category_label_ar": "شوهد مؤخرًا",
                "category_sort_order": 3,
            },
            {
                **base,
                "id": _uuid(),
                "title_en": "Your Favorite Vehicle",
                "title_ar": "مركبتك المفضلة",
                "badge_en": "Favorite",
                "badge_ar": "المفضلة",
                "category_key": "favorites",
                "category_label_en": "Your Favorites",
                "category_label_ar": "مفضلاتك",
                "category_sort_order": 4,
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM featured_auctions
            WHERE category_key IN ('recommended', 'recently_viewed', 'favorites')
            """
        )
    )
    op.drop_column("featured_auctions", "category_sort_order")
    op.drop_column("featured_auctions", "countdown_label")
    op.drop_column("featured_auctions", "bid_amount")
    op.drop_column("featured_auctions", "location_ar")
    op.drop_column("featured_auctions", "location_en")
    op.drop_column("featured_auctions", "mileage")
    op.drop_column("featured_auctions", "lot_number")
    op.drop_column("featured_auctions", "detail_url")
    op.drop_column("featured_auctions", "visibility")
    op.drop_column("featured_auctions", "category_label_ar")
    op.drop_column("featured_auctions", "category_label_en")
    op.drop_column("featured_auctions", "category_key")
