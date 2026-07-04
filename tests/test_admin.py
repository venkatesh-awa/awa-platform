from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from httpx import AsyncClient

from models.admin import AdminDashboardCard, AdminNavItem


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
        url=url,
        sort_order=1,
        is_active=True,
    )


async def test_get_admin_nav_returns_english_labels_by_default(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_nav_item("Home", "الرئيسية", "/")]
    )

    response = await client.get("/api/v1/admin/nav")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "Home"


async def test_get_admin_nav_returns_arabic_labels_when_requested(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_nav_item("Sellers", "البائعون", "/admin/sellers")]
    )

    response = await client.get("/api/v1/admin/nav?lang=ar")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "البائعون"


async def test_get_admin_dashboard_cards_filters_by_section(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result(
        [_dashboard_card("Add a New Car", "إضافة سيارة جديدة", "/admin/sellers/add-a-new-car")]
    )

    response = await client.get("/api/v1/admin/dashboard-cards?section=sellers")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["label"] == "Add a New Car"
    assert body[0]["section_key"] == "sellers"
    assert body[0]["url"] == "/admin/sellers/add-a-new-car"


async def test_get_admin_dashboard_cards_requires_section_query_param(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    response = await client.get("/api/v1/admin/dashboard-cards")

    assert response.status_code == 422
