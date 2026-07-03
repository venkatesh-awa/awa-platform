from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from httpx import AsyncClient

from models.auction import Auction
from models.content import FeaturedAuction, FooterLink, FooterSettings, MenuItem


def _mock_scalars_result(items: list) -> MagicMock:
    scalars = MagicMock()
    scalars.all.return_value = items
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


def _mock_scalar_one_or_none(value) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _menu_item(label_en: str, label_ar: str, url: str, children: list | None = None) -> MenuItem:
    item = MenuItem(
        id=uuid.uuid4(),
        label_en=label_en,
        label_ar=label_ar,
        url=url,
        opens_new_tab=False,
        is_active=True,
    )
    item.children = children or []
    return item


async def test_get_menu_returns_english_labels_by_default(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    child = _menu_item("Online Auctions", "مزادات على الانترنت", "/vehicles")
    parent = _menu_item("All Auctions", "جميع المزادات", "#", children=[child])
    mock_db_session.execute.return_value = _mock_scalars_result([parent])

    response = await client.get("/api/v1/content/menu")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["label"] == "All Auctions"
    assert body[0]["children"][0]["label"] == "Online Auctions"


async def test_get_menu_returns_arabic_labels_when_requested(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    parent = _menu_item("Home", "الصفحة الرئيسية", "/home")
    mock_db_session.execute.return_value = _mock_scalars_result([parent])

    response = await client.get("/api/v1/content/menu?lang=ar")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "الصفحة الرئيسية"


async def test_get_footer_returns_404_when_not_configured(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalar_one_or_none(None)

    response = await client.get("/api/v1/content/footer")

    assert response.status_code == 404


async def test_get_footer_returns_localized_content(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    settings = FooterSettings(
        id=uuid.uuid4(),
        about_text_en="About EN",
        about_text_ar="About AR",
        copyright_en="(c) EN",
        copyright_ar="(c) AR",
        support_phone="+971 8006006",
        support_email="support@alwataneya.ae",
        facebook_url=None,
        instagram_url=None,
        youtube_url=None,
        app_store_url=None,
        google_play_url=None,
    )
    link = FooterLink(
        id=uuid.uuid4(),
        section="quick_links",
        label_en="FAQs",
        label_ar="الأسئلة الشائعة",
        url="/faqs",
        is_active=True,
    )
    mock_db_session.execute.side_effect = [
        _mock_scalar_one_or_none(settings),
        _mock_scalars_result([link]),
    ]

    response = await client.get("/api/v1/content/footer?lang=ar")

    assert response.status_code == 200
    body = response.json()
    assert body["about_text"] == "About AR"
    assert body["links"][0]["label"] == "الأسئلة الشائعة"


async def test_get_home_aggregates_all_sections(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.side_effect = [
        _mock_scalars_result([]),  # categories
        _mock_scalars_result([]),  # featured auctions
        _mock_scalars_result([]),  # how it works
        _mock_scalars_result([]),  # value-added services
    ]

    response = await client.get("/api/v1/content/home")

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "auction_categories",
        "featured_auctions",
        "how_it_works",
        "value_added_services",
    }


async def test_featured_auction_includes_live_price_when_linked(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    auction = Auction(
        id=uuid.uuid4(),
        vehicle_id=uuid.uuid4(),
        status="live",
        starting_price=Decimal("25000.00"),
        reserve_price=None,
    )
    featured = FeaturedAuction(
        id=uuid.uuid4(),
        auction_id=auction.id,
        title_en="Hot Item",
        title_ar="رائج",
        badge_en="Hot",
        badge_ar="رائج",
        is_active=True,
    )
    featured.auction = auction
    mock_db_session.execute.side_effect = [
        _mock_scalars_result([]),  # categories
        _mock_scalars_result([featured]),  # featured auctions
        _mock_scalars_result([]),  # how it works
        _mock_scalars_result([]),  # value-added services
    ]

    response = await client.get("/api/v1/content/home")

    assert response.status_code == 200
    item = response.json()["featured_auctions"][0]
    assert item["status"] == "live"
    assert item["starting_price"] == "25000.00"


async def test_featured_auction_omits_price_when_not_linked(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    featured = FeaturedAuction(
        id=uuid.uuid4(),
        auction_id=None,
        title_en="Newly Listed Vehicles",
        title_ar="مركبات مدرجة حديثًا",
        badge_en="New",
        badge_ar="جديد",
        is_active=True,
    )
    featured.auction = None
    mock_db_session.execute.side_effect = [
        _mock_scalars_result([]),
        _mock_scalars_result([featured]),
        _mock_scalars_result([]),
        _mock_scalars_result([]),
    ]

    response = await client.get("/api/v1/content/home")

    assert response.status_code == 200
    item = response.json()["featured_auctions"][0]
    assert item["status"] is None
    assert item["starting_price"] is None
