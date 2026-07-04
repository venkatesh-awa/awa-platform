from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from httpx import AsyncClient

from models.auction import Auction
from models.content import FeaturedAuction, FooterLink, FooterSettings, MenuItem, VehicleListing


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
    child = _menu_item("Online Auctions", "Online Auctions AR", "/vehicles")
    parent = _menu_item("All Auctions", "All Auctions AR", "#", children=[child])
    mock_db_session.execute.return_value = _mock_scalars_result([parent])

    response = await client.get("/api/v1/content/menu")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["label"] == "All Auctions"
    assert body[0]["children"][0]["label"] == "Online Auctions"


async def test_get_menu_returns_arabic_labels_when_requested(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    parent = _menu_item("Home", "Home AR", "/home")
    mock_db_session.execute.return_value = _mock_scalars_result([parent])

    response = await client.get("/api/v1/content/menu?lang=ar")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "Home AR"


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
        label_ar="FAQs AR",
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
    assert body["links"][0]["label"] == "FAQs AR"


async def test_get_home_aggregates_all_sections(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.side_effect = [
        _mock_scalars_result([]),
        _mock_scalars_result([]),
        _mock_scalars_result([]),
        _mock_scalars_result([]),
    ]

    response = await client.get("/api/v1/content/home")

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "auction_categories",
        "featured_auctions",
        "how_it_works",
        "value_added_services",
    }


async def test_home_returns_featured_auction_tabs_without_card_data(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    featured = FeaturedAuction(
        id=uuid.uuid4(),
        auction_id=None,
        vehicle_listing_id=uuid.uuid4(),
        category_key="newly_listed",
        category_label_en="Newly Listed Vehicles",
        category_label_ar="Newly Listed Vehicles AR",
        visibility="all",
        category_sort_order=3,
        is_active=True,
    )
    mock_db_session.execute.side_effect = [
        _mock_scalars_result([]),
        _mock_scalars_result([featured]),
        _mock_scalars_result([]),
        _mock_scalars_result([]),
    ]

    response = await client.get("/api/v1/content/home")

    assert response.status_code == 200
    item = response.json()["featured_auctions"][0]
    assert item == {
        "id": str(featured.id),
        "category_key": "newly_listed",
        "category_label": "Newly Listed Vehicles",
        "visibility": "all",
        "sort_order": 3,
    }
    assert "title" not in item
    assert "lot_number" not in item


async def test_home_deduplicates_featured_auction_tabs(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    first = FeaturedAuction(
        id=uuid.uuid4(),
        category_key="ending_soon",
        category_label_en="Ending Soon",
        category_label_ar="Ending Soon AR",
        visibility="all",
        category_sort_order=1,
        is_active=True,
    )
    second = FeaturedAuction(
        id=uuid.uuid4(),
        category_key="ending_soon",
        category_label_en="Ending Soon",
        category_label_ar="Ending Soon AR",
        visibility="all",
        category_sort_order=1,
        is_active=True,
    )
    mock_db_session.execute.side_effect = [
        _mock_scalars_result([]),
        _mock_scalars_result([first, second]),
        _mock_scalars_result([]),
        _mock_scalars_result([]),
    ]

    response = await client.get("/api/v1/content/home")

    assert response.status_code == 200
    assert len(response.json()["featured_auctions"]) == 1


async def test_featured_auction_items_include_live_price_when_linked(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    vehicle_listing_id = uuid.uuid4()
    auction = Auction(
        id=uuid.uuid4(),
        vehicle_id=vehicle_listing_id,
        status="live",
        starting_price=Decimal("25000.00"),
        reserve_price=None,
    )
    featured = FeaturedAuction(
        id=uuid.uuid4(),
        auction_id=auction.id,
        vehicle_listing_id=vehicle_listing_id,
        badge_en="Hot",
        badge_ar="Hot AR",
        category_key="hot_items",
        category_label_en="Hot Items",
        category_label_ar="Hot Items AR",
        is_active=True,
    )
    featured.auction = auction
    featured.vehicle_listing = VehicleListing(
        id=featured.vehicle_listing_id,
        title_en="Toyota Land Cruiser 2025",
        title_ar="Toyota Land Cruiser 2025 AR",
        image_url=None,
        detail_url="/seller-buyer/vehicle-details/102684",
        lot_number="102684",
        mileage="100002 KM",
        location_en="Abu Dhabi",
        location_ar="Abu Dhabi AR",
        bid_amount="AED 5,500",
        countdown_label="3D: 2H: 48M: 46S",
        is_active=True,
    )
    mock_db_session.execute.return_value = _mock_scalars_result([featured])

    response = await client.get("/api/v1/content/featured-auctions/hot_items/items")

    assert response.status_code == 200
    item = response.json()[0]
    assert item["status"] == "live"
    assert item["starting_price"] == "25000.00"
    assert item["title"] == "Toyota Land Cruiser 2025"


async def test_featured_auction_items_ignore_auction_when_vehicle_mismatched(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    """auction_id and vehicle_listing_id are independent nullable links, so a
    stale edit can point them at two different vehicles. The card should show
    the linked vehicle but must not surface the mismatched auction's status/price.
    """
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
        vehicle_listing_id=uuid.uuid4(),
        badge_en="Hot",
        badge_ar="Hot AR",
        category_key="hot_items",
        category_label_en="Hot Items",
        category_label_ar="Hot Items AR",
        is_active=True,
    )
    featured.auction = auction
    featured.vehicle_listing = VehicleListing(
        id=featured.vehicle_listing_id,
        title_en="Toyota Land Cruiser 2025",
        title_ar="Toyota Land Cruiser 2025 AR",
        image_url=None,
        detail_url="/seller-buyer/vehicle-details/102684",
        lot_number="102684",
        mileage="100002 KM",
        location_en="Abu Dhabi",
        location_ar="Abu Dhabi AR",
        bid_amount="AED 5,500",
        countdown_label="3D: 2H: 48M: 46S",
        is_active=True,
    )
    mock_db_session.execute.return_value = _mock_scalars_result([featured])

    response = await client.get("/api/v1/content/featured-auctions/hot_items/items")

    assert response.status_code == 200
    item = response.json()[0]
    assert item["title"] == "Toyota Land Cruiser 2025"
    assert item["status"] is None
    assert item["starting_price"] is None


async def test_featured_auction_items_come_from_vehicle_listings(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    featured = FeaturedAuction(
        id=uuid.uuid4(),
        auction_id=None,
        vehicle_listing_id=uuid.uuid4(),
        badge_en="Recommended",
        badge_ar="Recommended AR",
        category_key="recommended",
        category_label_en="Recommended",
        category_label_ar="Recommended AR",
        visibility="authenticated",
        is_active=True,
    )
    featured.auction = None
    featured.vehicle_listing = VehicleListing(
        id=featured.vehicle_listing_id,
        title_en="Toyota Land Cruiser 2025",
        title_ar="Toyota Land Cruiser 2025 AR",
        image_url="https://example.test/vehicle.jpg",
        detail_url="/seller-buyer/vehicle-details/102684",
        lot_number="102684",
        mileage="100002 KM",
        location_en="Abu Dhabi",
        location_ar="Abu Dhabi AR",
        bid_amount="AED 5,500",
        countdown_label="3D: 2H: 48M: 46S",
        is_active=True,
    )
    mock_db_session.execute.return_value = _mock_scalars_result([featured])

    response = await client.get("/api/v1/content/featured-auctions/recommended/items")

    assert response.status_code == 200
    item = response.json()[0]
    assert item["vehicle_listing_id"] == str(featured.vehicle_listing_id)
    assert item["title"] == "Toyota Land Cruiser 2025"
    assert item["detail_url"] == "/seller-buyer/vehicle-details/102684"
    assert item["lot_number"] == "102684"
    assert item["mileage"] == "100002 KM"
    assert item["location"] == "Abu Dhabi"
    assert item["bid_amount"] == "AED 5,500"


async def test_featured_auction_items_skip_rows_without_vehicle_listing(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    featured = FeaturedAuction(
        id=uuid.uuid4(),
        auction_id=None,
        vehicle_listing_id=None,
        category_key="recommended",
        category_label_en="Recommended",
        category_label_ar="Recommended AR",
        visibility="authenticated",
        is_active=True,
    )
    featured.auction = None
    featured.vehicle_listing = None
    mock_db_session.execute.return_value = _mock_scalars_result([featured])

    response = await client.get("/api/v1/content/featured-auctions/recommended/items")

    assert response.status_code == 200
    assert response.json() == []
