from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import MagicMock

from httpx import AsyncClient


def _mock_scalars_result(items: list) -> MagicMock:
    scalars = MagicMock()
    scalars.all.return_value = items
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


def _mock_scalar_one_result(value) -> MagicMock:
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _mock_grouped_counts_result(rows: list[tuple[str, int]]) -> MagicMock:
    result = MagicMock()
    result.all.return_value = rows
    return result


def _record(lot_no: str = "100288", payment_status: str = "pending_buyer_payment") -> MagicMock:
    row = MagicMock()
    row.id = uuid.uuid4()
    row.lot_no = lot_no
    row.chassis_number = "021225191836429"
    row.title = "Buick Other 2019"
    row.year_of_make = 2019
    row.buyer_name = "S V Krishna Reddy"
    row.buyer_email = "krishnareddy0296@example.com"
    row.seller_name = "Rajesh Meesarapu"
    row.seller_email = "dhanasri0911@example.com"
    row.payment_status = payment_status
    row.payment_due_date = date(2026, 6, 24)
    row.location = "Dubai"
    row.max_bid = "3900.00"
    return row


async def test_get_vehicle_payment_status_count_returns_counts_per_status(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_grouped_counts_result(
        [("paid_awaiting_documents", 2), ("pending_buyer_payment", 5)]
    )

    response = await client.get("/api/v1/admin/vehicle-payment-status-count")

    assert response.status_code == 200
    body = response.json()
    assert body["paid_awaiting_documents"] == 2
    assert body["pending_buyer_payment"] == 5
    assert body["paid_documents_ready_pending_deliver"] == 0
    assert body["pending_seller_payment"] == 0


async def test_get_vehicle_payment_status_returns_paginated_records(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.side_effect = [
        _mock_scalar_one_result(1),
        _mock_scalars_result([_record()]),
    ]

    response = await client.get("/api/v1/admin/vehicle-payment-status?status=ALL&page=1&page_size=50")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["total_pages"] == 1
    assert body["records"][0]["lot_no"] == "100288"
    assert body["records"][0]["payment_status"] == "pending_buyer_payment"


async def test_get_vehicle_payment_status_filters_by_status(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.side_effect = [
        _mock_scalar_one_result(1),
        _mock_scalars_result([_record(payment_status="paid_awaiting_documents")]),
    ]

    response = await client.get(
        "/api/v1/admin/vehicle-payment-status?status=paid_awaiting_documents&page=1&page_size=50"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["records"][0]["payment_status"] == "paid_awaiting_documents"


async def test_get_vehicle_in_store_returns_paginated_records(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.side_effect = [
        _mock_scalar_one_result(1),
        _mock_scalars_result([_record(lot_no="103147")]),
    ]

    response = await client.get("/api/v1/admin/vehicle-in-store?page=1&page_size=50")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["records"][0]["id"] == "103147"
    assert body["records"][0]["chassis_number"] == "021225191836429"
    assert body["records"][0]["title"] == "Buick Other 2019"
    assert body["records"][0]["location"] == "Dubai"
    assert "payment_status" not in body["records"][0]


async def test_get_vehicle_in_store_filters_by_id(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.side_effect = [
        _mock_scalar_one_result(1),
        _mock_scalars_result([_record(lot_no="103147")]),
    ]

    response = await client.get("/api/v1/admin/vehicle-in-store?id=103147")

    assert response.status_code == 200
    assert response.json()["records"][0]["id"] == "103147"
