"""content tables - menu, categories, featured auctions, how it works,
value-added services, footer - seeded from the live seller-buyer/home page

Revision ID: 0002_content_tables
Revises: 0001_initial
Create Date: 2026-07-03

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_content_tables"
down_revision: str | None = "0001_initial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def upgrade() -> None:
    menu_items = op.create_table(
        "menu_items",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "parent_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("menu_items.id", ondelete="NO ACTION"),
            nullable=True,
        ),
        sa.Column("label_en", sa.Unicode(length=100), nullable=False),
        sa.Column("label_ar", sa.Unicode(length=100), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("opens_new_tab", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_menu_items_parent_id", "menu_items", ["parent_id"])

    categories = op.create_table(
        "auction_categories",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name_en", sa.Unicode(length=100), nullable=False),
        sa.Column("name_ar", sa.Unicode(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    featured_auctions = op.create_table(
        "featured_auctions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "auction_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("auctions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title_en", sa.Unicode(length=200), nullable=False),
        sa.Column("title_ar", sa.Unicode(length=200), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("badge_en", sa.Unicode(length=50), nullable=True),
        sa.Column("badge_ar", sa.Unicode(length=50), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_featured_auctions_auction_id", "featured_auctions", ["auction_id"])

    how_it_works_steps = op.create_table(
        "how_it_works_steps",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("title_en", sa.Unicode(length=150), nullable=False),
        sa.Column("title_ar", sa.Unicode(length=150), nullable=False),
        sa.Column("description_en", sa.Unicode(length=500), nullable=False),
        sa.Column("description_ar", sa.Unicode(length=500), nullable=False),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    value_added_services = op.create_table(
        "value_added_services",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name_en", sa.Unicode(length=150), nullable=False),
        sa.Column("name_ar", sa.Unicode(length=150), nullable=False),
        sa.Column("description_en", sa.Unicode(length=500), nullable=True),
        sa.Column("description_ar", sa.Unicode(length=500), nullable=True),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    footer_settings = op.create_table(
        "footer_settings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("about_text_en", sa.Unicode(length=1000), nullable=False),
        sa.Column("about_text_ar", sa.Unicode(length=1000), nullable=False),
        sa.Column("copyright_en", sa.Unicode(length=200), nullable=False),
        sa.Column("copyright_ar", sa.Unicode(length=200), nullable=False),
        sa.Column("support_phone", sa.String(length=50), nullable=True),
        sa.Column("support_email", sa.String(length=200), nullable=True),
        sa.Column("facebook_url", sa.String(length=500), nullable=True),
        sa.Column("instagram_url", sa.String(length=500), nullable=True),
        sa.Column("youtube_url", sa.String(length=500), nullable=True),
        sa.Column("app_store_url", sa.String(length=500), nullable=True),
        sa.Column("google_play_url", sa.String(length=500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    footer_links = op.create_table(
        "footer_links",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("section", sa.String(length=50), nullable=False, server_default="quick_links"),
        sa.Column("label_en", sa.Unicode(length=150), nullable=False),
        sa.Column("label_ar", sa.Unicode(length=150), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    _seed(
        menu_items=menu_items,
        categories=categories,
        featured_auctions=featured_auctions,
        how_it_works_steps=how_it_works_steps,
        value_added_services=value_added_services,
        footer_settings=footer_settings,
        footer_links=footer_links,
    )


def _seed(
    *,
    menu_items: sa.Table,
    categories: sa.Table,
    featured_auctions: sa.Table,
    how_it_works_steps: sa.Table,
    value_added_services: sa.Table,
    footer_settings: sa.Table,
    footer_links: sa.Table,
) -> None:
    # --- Menu (mirrors live seller-buyer/home nav) ---
    all_auctions_id = _uuid()
    help_id = _uuid()
    op.bulk_insert(
        menu_items,
        [
            {
                "id": _uuid(),
                "parent_id": None,
                "label_en": "Home",
                "label_ar": "الصفحة الرئيسية",
                "url": "/",
                "opens_new_tab": False,
                "sort_order": 1,
            },
            {
                "id": all_auctions_id,
                "parent_id": None,
                "label_en": "All Auctions",
                "label_ar": "جميع المزادات",
                "url": "/seller-buyer/all-auction/vehicles",
                "opens_new_tab": False,
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "parent_id": None,
                "label_en": "Sell Your Car",
                "label_ar": "بيع سيارتك",
                "url": "/seller-buyer/sell-car",
                "opens_new_tab": False,
                "sort_order": 3,
            },
            {
                "id": help_id,
                "parent_id": None,
                "label_en": "Help",
                "label_ar": "المساعدة",
                "url": "#",
                "opens_new_tab": False,
                "sort_order": 4,
            },
            {
                "id": _uuid(),
                "parent_id": None,
                "label_en": "Sign Up",
                "label_ar": "إنشاء حساب",
                "url": "/sign-up",
                "opens_new_tab": False,
                "sort_order": 5,
            },
            {
                "id": _uuid(),
                "parent_id": None,
                "label_en": "Log In",
                "label_ar": "تسجيل الدخول",
                "url": "login",
                "opens_new_tab": False,
                "sort_order": 6,
            },
            # All Auctions dropdown
            {
                "id": _uuid(),
                "parent_id": all_auctions_id,
                "label_en": "Online Auctions",
                "label_ar": "مزادات على الانترنت",
                "url": "/seller-buyer/all-auction/vehicles",
                "opens_new_tab": False,
                "sort_order": 1,
            },
            {
                "id": _uuid(),
                "parent_id": all_auctions_id,
                "label_en": "Silent Auctions",
                "label_ar": "المزاد الصامت",
                "url": "/seller-buyer/all-auction/silent-auctions",
                "opens_new_tab": False,
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "parent_id": all_auctions_id,
                "label_en": "Equipment & Machinery",
                "label_ar": "الآليات والمعدات",
                "url": "/seller-buyer/all-auction/equipment-machinery",
                "opens_new_tab": False,
                "sort_order": 3,
            },
            {
                "id": _uuid(),
                "parent_id": all_auctions_id,
                "label_en": "Emirates Moto",
                "label_ar": "الإمارات موتو",
                "url": "https://emiratesmoto.ae/",
                "opens_new_tab": True,
                "sort_order": 4,
            },
            # Help dropdown
            {
                "id": _uuid(),
                "parent_id": help_id,
                "label_en": "FAQs",
                "label_ar": "الأسئلة الشائعة",
                "url": "/seller-buyer/auctions/faqs",
                "opens_new_tab": False,
                "sort_order": 1,
            },
            {
                "id": _uuid(),
                "parent_id": help_id,
                "label_en": "About Us",
                "label_ar": "عن الوطنية",
                "url": "/seller-buyer/about-wataneya",
                "opens_new_tab": False,
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "parent_id": help_id,
                "label_en": "Find Branches",
                "label_ar": "أقرب فرع",
                "url": "/seller-buyer/auctions/help/find-branch",
                "opens_new_tab": False,
                "sort_order": 3,
            },
            {
                "id": _uuid(),
                "parent_id": help_id,
                "label_en": "Contact Us",
                "label_ar": "تواصل معنا",
                "url": "/seller-buyer/auctions/help/Contact-us",
                "opens_new_tab": False,
                "sort_order": 4,
            },
        ],
    )

    # --- Auction categories ---
    op.bulk_insert(
        categories,
        [
            {
                "id": _uuid(),
                "name_en": "Online Auctions",
                "name_ar": "مزادات على الانترنت",
                "slug": "online-auctions",
                "icon_url": None,
                "link_url": "/seller-buyer/all-auction/vehicles",
                "sort_order": 1,
            },
            {
                "id": _uuid(),
                "name_en": "Silent Auctions",
                "name_ar": "المزاد الصامت",
                "slug": "silent-auctions",
                "icon_url": None,
                "link_url": "/seller-buyer/all-auction/silent-auctions",
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "name_en": "UAE Plates",
                "name_ar": "لوحات المركبات",
                "slug": "uae-plates",
                "icon_url": None,
                "link_url": "/seller-buyer/coming-soon",
                "sort_order": 3,
            },
            {
                "id": _uuid(),
                "name_en": "Equipment & Machinery",
                "name_ar": "الآليات والمعدات",
                "slug": "equipment-machinery",
                "icon_url": None,
                "link_url": "/seller-buyer/coming-soon",
                "sort_order": 4,
            },
            {
                "id": _uuid(),
                "name_en": "Emirates Moto",
                "name_ar": "الإمارات موتو",
                "slug": "emirates-moto",
                "icon_url": None,
                "link_url": "https://emiratesmoto.ae/",
                "sort_order": 5,
            },
        ],
    )

    # --- Featured auctions: editorial placeholders, no live auction linked yet ---
    op.bulk_insert(
        featured_auctions,
        [
            {
                "id": _uuid(),
                "auction_id": None,
                "title_en": "Newly Listed Vehicles",
                "title_ar": "مركبات مدرجة حديثًا",
                "image_url": None,
                "badge_en": "New",
                "badge_ar": "جديد",
                "sort_order": 1,
            },
            {
                "id": _uuid(),
                "auction_id": None,
                "title_en": "Ending Soon",
                "title_ar": "ينتهي قريبًا",
                "image_url": None,
                "badge_en": "Ending Soon",
                "badge_ar": "ينتهي قريبًا",
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "auction_id": None,
                "title_en": "Hot Items",
                "title_ar": "الأكثر رواجًا",
                "image_url": None,
                "badge_en": "Hot",
                "badge_ar": "رائج",
                "sort_order": 3,
            },
        ],
    )

    # --- How It Works ---
    op.bulk_insert(
        how_it_works_steps,
        [
            {
                "id": _uuid(),
                "step_number": 1,
                "title_en": "Sign Up & Verify Account",
                "title_ar": "إنشاء حساب وتوثيقه",
                "description_en": "Create your account and complete verification in minutes to start bidding.",
                "description_ar": "أنشئ حسابك وأكمل التوثيق خلال دقائق لتبدأ بالمزايدة.",
                "icon_url": None,
                "sort_order": 1,
            },
            {
                "id": _uuid(),
                "step_number": 2,
                "title_en": "Browse & Place Bids",
                "title_ar": "تصفح المزادات وقدم عروضك",
                "description_en": "Explore our extensive inventory and place competitive bids on your desired vehicles.",
                "description_ar": "تصفح مجموعتنا الواسعة وقدم عروض تنافسية على المركبات التي تريدها.",
                "icon_url": None,
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "step_number": 3,
                "title_en": "Win & Make Payment",
                "title_ar": "الفوز والدفع",
                "description_en": "Won the auction? Complete your payment securely through our trusted platform.",
                "description_ar": "هل فزت بالمزاد؟ أكمل الدفع بأمان عبر منصتنا الموثوقة.",
                "icon_url": None,
                "sort_order": 3,
            },
            {
                "id": _uuid(),
                "step_number": 4,
                "title_en": "Get Your Car Delivered",
                "title_ar": "توصيل السيارة إلى باب منزلك",
                "description_en": "Sit back and relax as we handle the delivery of your vehicle to your doorstep.",
                "description_ar": "استرخِ ودعنا نتولى توصيل مركبتك إلى باب منزلك.",
                "icon_url": None,
                "sort_order": 4,
            },
        ],
    )

    # --- Value-added services ---
    op.bulk_insert(
        value_added_services,
        [
            {
                "id": _uuid(),
                "name_en": "Vehicle Inspection",
                "name_ar": "فحص المركبات",
                "description_en": None,
                "description_ar": None,
                "icon_url": None,
                "link_url": "/seller-buyer/upcoming-page",
                "sort_order": 1,
            },
            {
                "id": _uuid(),
                "name_en": "Vehicle Delivery",
                "name_ar": "خدمة توصيل المركبة",
                "description_en": None,
                "description_ar": None,
                "icon_url": None,
                "link_url": "/seller-buyer/vehicle-delivery",
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "name_en": "Ownership Transfer",
                "name_ar": "خدمة نقل ملكية المركبة",
                "description_en": None,
                "description_ar": None,
                "icon_url": None,
                "link_url": "/seller-buyer/upcoming-page",
                "sort_order": 3,
            },
            {
                "id": _uuid(),
                "name_en": "Polishing & Detailing",
                "name_ar": "تلميع وتفاصيل المركبة",
                "description_en": None,
                "description_ar": None,
                "icon_url": None,
                "link_url": "/seller-buyer/upcoming-page",
                "sort_order": 4,
            },
            {
                "id": _uuid(),
                "name_en": "Maintenance & Repairs",
                "name_ar": "صيانة وإصلاح المركبة",
                "description_en": None,
                "description_ar": None,
                "icon_url": None,
                "link_url": "/seller-buyer/upcoming-page",
                "sort_order": 5,
            },
            {
                "id": _uuid(),
                "name_en": "More Services",
                "name_ar": "المزيد من الخدمات",
                "description_en": None,
                "description_ar": None,
                "icon_url": None,
                "link_url": "/seller-buyer/upcoming-page",
                "sort_order": 6,
            },
        ],
    )

    # --- Footer ---
    op.bulk_insert(
        footer_settings,
        [
            {
                "id": _uuid(),
                "about_text_en": (
                    "Al Wataneya Auctions, established in 2010 by Emirates Transport, is a "
                    "leading UAE vehicle auction platform, offering diverse vehicles for "
                    "individuals & businesses."
                ),
                "about_text_ar": "تأسست شركة الوطنية للمزادات في عام 2010 من قبل مؤسسة الإمارات للنقل، وهي منصة رائدة للمزادات في دولة الإمارات تقدم مركبات متنوعة للأفراد والشركات.",
                "copyright_en": "© 2025 All rights reserved",
                "copyright_ar": "© 2025 جميع الحقوق محفوظة",
                "support_phone": "+971 8006006",
                "support_email": "support@alwataneya.ae",
                "facebook_url": "https://facebook.com/alwataneya.auctions",
                "instagram_url": "https://instagram.com/alwataneya.auctions",
                "youtube_url": "https://www.youtube.com/channel/UCGtQXjGZIfmGNb-67TnYS4g",
                "app_store_url": None,
                "google_play_url": None,
            }
        ],
    )

    op.bulk_insert(
        footer_links,
        [
            {
                "id": _uuid(),
                "section": "quick_links",
                "label_en": "About Al Wataneya",
                "label_ar": "عن الوطنية",
                "url": "/seller-buyer/about-wataneya",
                "sort_order": 1,
            },
            {
                "id": _uuid(),
                "section": "quick_links",
                "label_en": "Terms & Conditions",
                "label_ar": "الشروط والأحكام",
                "url": "/seller-buyer/term",
                "sort_order": 2,
            },
            {
                "id": _uuid(),
                "section": "quick_links",
                "label_en": "FAQs",
                "label_ar": "الأسئلة الشائعة",
                "url": "/seller-buyer/auctions/faqs",
                "sort_order": 3,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("footer_links")
    op.drop_table("footer_settings")
    op.drop_table("value_added_services")
    op.drop_table("how_it_works_steps")
    op.drop_table("featured_auctions")
    op.drop_table("auction_categories")
    op.drop_table("menu_items")
