"""create and seed vehicle_status_metrics for the vehicle real-time / MTD /
payment-summary dashboard tiles

Revision ID: 0017_vehicle_status_metrics
Revises: 0016_admin_home_cards
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from urllib.parse import quote

import sqlalchemy as sa

from alembic import op

revision: str = "0017_vehicle_status_metrics"
down_revision: str | None = "0016_admin_home_cards"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_IMAGE_BASE = "https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _image(filename: str | None) -> str | None:
    return _IMAGE_BASE + quote(filename) if filename else None


# (stat_key, label_en, label_ar, icon_class, image filename, color_class)
# group_key == "realtime": the 5 top status tiles on the Vehicles Real-Time
# Status dashboard, keyed to match the *_count fields returned by the
# reporting endpoint.
_REALTIME: list[tuple[str, str, str, str | None, str | None, str]] = [
    ("in_yard_count", "In Yard", "في الساحة", None, "entrances 2.png", "bg-primary"),
    ("in_inspection_count", "Inspection", "الفحص", None, "Vector.png", "bg-success"),
    ("in_washing_count", "Washing", "الغسيل", None, "car-wash.png", "bg-danger"),
    ("in_live_auction_count", "Auction", "المزاد", None, "mingcute_auction-fill.svg", "bg-dark"),
    (
        "in_seller_unapproved_count",
        "Pending Approval",
        "بانتظار الموافقة",
        None,
        "streamline-sharp-color_time-lapse.png",
        "bg-pending",
    ),
]

# group_key == "mtd": the month-to-date summary tiles.
_MTD: list[tuple[str, str, str, str | None, str | None, str]] = [
    ("vehicle_received", "Approved", "تمت الموافقة", "fa fa-check", None, "bg-success"),
    ("internal_vehicle_received", "Delivered", "تم التسليم", "fa fa-money-bill", None, "bg-info"),
    ("total_auctions", "Paid", "مدفوع", "fa fa-car", None, "bg-primary"),
    ("in_seller_approved_count", "Seller Approve", "موافقة البائع", "fa fa-exclamation", None, "bg-warning"),
    ("is_buyer_paid", "Buyer Paid", "دفع المشتري", None, "paid.png", None),
    ("paid_not_delivered", "Pending Payment", "الدفع معلق", None, "pending payments.png", None),
    ("delivered", "Paid Delivered", "تم الدفع والتسليم", None, "delivered.png", None),
]

# group_key == "payment_summary": the 4 tiles on the buyer-payment-status
# dashboard.
_PAYMENT_SUMMARY: list[tuple[str, str, str, str | None, str | None, str]] = [
    (
        "paid_awaiting_documents",
        "Paid - Awaiting Documents",
        "مدفوع - بانتظار المستندات",
        None,
        "entrances 2.png",
        "bg-primary",
    ),
    (
        "paid_documents_ready_pending_deliver",
        "Paid - Documents Ready",
        "مدفوع - المستندات جاهزة",
        None,
        "Vector.png",
        "bg-success",
    ),
    (
        "pending_buyer_payment",
        "Pending Buyer Payment",
        "بانتظار دفع المشتري",
        None,
        "car-wash.png",
        "bg-danger",
    ),
    (
        "pending_seller_payment",
        "Pending Seller Payment",
        "بانتظار دفع البائع",
        None,
        "car-wash.png",
        "bg-danger",
    ),
]

_GROUPS: list[tuple[str, list[tuple[str, str, str, str | None, str | None, str]]]] = [
    ("realtime", _REALTIME),
    ("mtd", _MTD),
    ("payment_summary", _PAYMENT_SUMMARY),
]


def upgrade() -> None:
    op.create_table(
        "vehicle_status_metrics",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("group_key", sa.String(length=50), nullable=False, index=True),
        sa.Column("stat_key", sa.String(length=100), nullable=False),
        sa.Column("label_en", sa.Unicode(length=150), nullable=False),
        sa.Column("label_ar", sa.Unicode(length=150), nullable=False),
        sa.Column("icon_class", sa.String(length=100), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("color_class", sa.String(length=50), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    metrics = sa.table(
        "vehicle_status_metrics",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("group_key", sa.String(length=50)),
        sa.column("stat_key", sa.String(length=100)),
        sa.column("label_en", sa.Unicode(length=150)),
        sa.column("label_ar", sa.Unicode(length=150)),
        sa.column("icon_class", sa.String(length=100)),
        sa.column("image_url", sa.String(length=500)),
        sa.column("color_class", sa.String(length=50)),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )

    op.bulk_insert(
        metrics,
        [
            {
                "id": _uuid(),
                "group_key": group_key,
                "stat_key": stat_key,
                "label_en": label_en,
                "label_ar": label_ar,
                "icon_class": icon_class,
                "image_url": _image(image_filename),
                "color_class": color_class,
                "sort_order": sort_order,
                "is_active": True,
            }
            for group_key, rows in _GROUPS
            for sort_order, (stat_key, label_en, label_ar, icon_class, image_filename, color_class) in enumerate(
                rows, start=1
            )
        ],
    )


def downgrade() -> None:
    op.drop_table("vehicle_status_metrics")
