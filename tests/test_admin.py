from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from httpx import AsyncClient

from models.admin import AdminDashboardCard, AdminNavItem, VehicleStatusMetric


def _mock_scalars_result(items: list) -> MagicMock:
    scalars = MagicMock()
    scalars.all.return_value = items
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


def _nav_item(label_en: str, label_ar: str, url: str, sort_order: int = 1) -> AdminNavItem:
    return AdminNavItem(
        id=uuid.uuid4(),
        label_en=label_en,
        label_ar=label_ar,
        icon_class="fa-solid fa-house",
        url=url,
        sort_order=sort_order,
        is_active=True,
    )


def _dashboard_card(label_en: str, label_ar: str, url: str, section_key: str = "sellers") -> AdminDashboardCard:
    return AdminDashboardCard(
        id=uuid.uuid4(),
        section_key=section_key,
        label_en=label_en,
        label_ar=label_ar,
        description_en="Description EN",
        description_ar="Description AR",
        icon_class="fa-solid fa-car",
        image_url="https://example.com/image.png",
        url=url,
        sort_order=1,
        is_active=True,
    )


async def test_get_admin_nav_returns_english_labels_by_default(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_nav_item("Home", "الرئيسية", "/")]
    )

    response = await staff_client.get("/api/v1/admin/nav")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "Home"


async def test_get_admin_nav_returns_arabic_labels_when_requested(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_nav_item("Sellers", "البائعون", "/admin/sellers")]
    )

    response = await staff_client.get("/api/v1/admin/nav?lang=ar")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "البائعون"


async def test_get_admin_nav_hides_sections_the_caller_cant_access(
    make_role_client, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [
            _nav_item("Sellers", "البائعون", "/admin/sellers", sort_order=1),
            _nav_item("Management", "الإدارة", "/admin/management", sort_order=2),
            _nav_item("Accountant", "المحاسب", "/admin/accountant", sort_order=3),
        ]
    )

    async with make_role_client("Manager") as client:
        response = await client.get("/api/v1/admin/nav")

    assert response.status_code == 200
    labels = {item["label"] for item in response.json()}
    assert labels == {"Sellers", "Management"}


async def test_get_admin_nav_requires_staff_role(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    """`client` is a plain Buyer (tests/conftest.py's test_buyer fixture)."""
    response = await client.get("/api/v1/admin/nav")

    assert response.status_code == 403


async def test_get_admin_dashboard_cards_filters_by_section(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_dashboard_card("Add a New Car", "إضافة سيارة جديدة", "/admin/sellers/add-a-new-car")]
    )

    response = await staff_client.get("/api/v1/admin/dashboard-cards?section=sellers")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["label"] == "Add a New Car"
    assert body[0]["section_key"] == "sellers"
    assert body[0]["url"] == "/admin/sellers/add-a-new-car"
    assert body[0]["image_url"] == "https://example.com/image.png"


async def test_get_admin_dashboard_cards_requires_section_query_param(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    response = await staff_client.get("/api/v1/admin/dashboard-cards")

    assert response.status_code == 422


async def test_get_admin_dashboard_cards_requires_staff_role(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    response = await client.get("/api/v1/admin/dashboard-cards?section=sellers")

    assert response.status_code == 403


async def test_get_admin_dashboard_cards_accountant_section_blocks_manager(
    make_role_client, mock_db_session: MagicMock
) -> None:
    async with make_role_client("Manager") as client:
        response = await client.get("/api/v1/admin/dashboard-cards?section=accountant")

    assert response.status_code == 403


async def test_get_admin_dashboard_cards_accountant_section_allows_accountant(
    make_role_client, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result([])

    async with make_role_client("Accountant") as client:
        response = await client.get("/api/v1/admin/dashboard-cards?section=accountant")

    assert response.status_code == 200


async def test_get_admin_dashboard_cards_management_section_blocks_accountant(
    make_role_client, mock_db_session: MagicMock
) -> None:
    async with make_role_client("Accountant") as client:
        response = await client.get("/api/v1/admin/dashboard-cards?section=management")

    assert response.status_code == 403


async def test_get_admin_dashboard_cards_management_section_allows_manager(
    make_role_client, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result([])

    async with make_role_client("Manager") as client:
        response = await client.get("/api/v1/admin/dashboard-cards?section=management")

    assert response.status_code == 200


def _mock_scalar_result(value: int) -> MagicMock:
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


async def test_get_admin_user_counts_returns_all_four_buckets(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    # Service issues four count queries in order: total, sellers, buyers, staff.
    mock_db_session.execute.side_effect = [
        _mock_scalar_result(120),
        _mock_scalar_result(40),
        _mock_scalar_result(70),
        _mock_scalar_result(10),
    ]

    response = await staff_client.get("/api/v1/admin/user-counts")

    assert response.status_code == 200
    assert response.json() == {"total": 120, "sellers": 40, "buyers": 70, "staff": 10}


async def test_get_admin_user_counts_requires_staff_role(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    response = await client.get("/api/v1/admin/user-counts")

    assert response.status_code == 403


def _vehicle_status_metric(
    stat_key: str, label_en: str, label_ar: str, group_key: str = "realtime"
) -> VehicleStatusMetric:
    return VehicleStatusMetric(
        id=uuid.uuid4(),
        group_key=group_key,
        stat_key=stat_key,
        label_en=label_en,
        label_ar=label_ar,
        icon_class=None,
        image_url="https://uat-alwataneya.et.ae/PA_AdminDashboard/resource/images/entrances%202.png",
        color_class="bg-primary",
        sort_order=1,
        is_active=True,
    )


async def test_get_vehicle_status_metrics_returns_english_labels_by_default(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_vehicle_status_metric("in_yard_count", "In Yard", "في الساحة")]
    )

    response = await staff_client.get("/api/v1/admin/vehicle-status-metrics?group=realtime")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["label"] == "In Yard"
    assert body[0]["stat_key"] == "in_yard_count"
    assert body[0]["group_key"] == "realtime"
    assert body[0]["image_url"].startswith("https://uat-alwataneya.et.ae/")


async def test_get_vehicle_status_metrics_returns_arabic_labels_when_requested(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_vehicle_status_metric("in_yard_count", "In Yard", "في الساحة")]
    )

    response = await staff_client.get("/api/v1/admin/vehicle-status-metrics?group=realtime&lang=ar")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "في الساحة"


async def test_get_vehicle_status_metrics_requires_group_query_param(
    staff_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    response = await staff_client.get("/api/v1/admin/vehicle-status-metrics")

    assert response.status_code == 422


async def test_get_vehicle_status_metrics_requires_staff_role(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    response = await client.get("/api/v1/admin/vehicle-status-metrics?group=realtime")

    assert response.status_code == 403
