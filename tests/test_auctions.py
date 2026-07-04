from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from httpx import AsyncClient

from models.auction import Auction
from models.content import VehicleListing


def _make_auction(status_: str = "live") -> Auction:
    now = datetime.now(UTC)
    vehicle = VehicleListing(
        id=uuid.uuid4(),
        title_en="Toyota Land Cruiser 2025",
        title_ar="Toyota Land Cruiser 2025 AR",
        image_url=None,
        detail_url="/seller-buyer/vehicle-details/102684",
        lot_number="102684",
        mileage="100002 KM",
        location_en="Abu Dhabi",
        location_ar="Abu Dhabi AR",
        is_active=True,
    )
    auction = Auction(
        id=uuid.uuid4(),
        vehicle_id=vehicle.id,
        status=status_,
        starting_price=Decimal("10000.00"),
        reserve_price=None,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=1),
    )
    auction.vehicle = vehicle
    return auction


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


async def test_get_auction_not_found_returns_404(client: AsyncClient, mock_db_session: MagicMock) -> None:
    mock_db_session.execute.return_value = _mock_scalar_result(None)

    response = await client.get(f"/api/v1/auctions/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_auction_returns_auction(client: AsyncClient, mock_db_session: MagicMock) -> None:
    auction = _make_auction()
    mock_db_session.execute.return_value = _mock_scalar_result(auction)

    response = await client.get(f"/api/v1/auctions/{auction.id}")

    assert response.status_code == 200
    assert response.json()["status"] == "live"


async def test_submit_bid_rejects_zero_amount(client: AsyncClient, mock_db_session: MagicMock) -> None:
    auction = _make_auction()
    mock_db_session.execute.return_value = _mock_scalar_result(auction)

    response = await client.post(f"/api/v1/auctions/{auction.id}/bids", json={"amount": "0"})

    assert response.status_code == 422


async def test_submit_bid_rejects_when_auction_not_live(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    auction = _make_auction(status_="closed")
    mock_db_session.execute.return_value = _mock_scalar_result(auction)

    response = await client.post(f"/api/v1/auctions/{auction.id}/bids", json={"amount": "15000"})

    assert response.status_code == 409


async def test_submit_bid_publishes_to_kafka_and_returns_202(
    client: AsyncClient, mock_db_session: MagicMock, monkeypatch
) -> None:
    auction = _make_auction()
    mock_db_session.execute.return_value = _mock_scalar_result(auction)

    published: dict = {}

    async def fake_publish_event(topic: str, key: str, value: bytes) -> None:
        published["topic"] = topic
        published["key"] = key
        published["value"] = value

    monkeypatch.setattr("services.bid_service.publish_event", fake_publish_event)

    response = await client.post(f"/api/v1/auctions/{auction.id}/bids", json={"amount": "15000.50"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "received"
    assert published["key"] == str(auction.id)  # partition key must be auction_id for ordering


async def test_submit_bid_returns_503_when_kafka_unavailable(
    client: AsyncClient, mock_db_session: MagicMock, monkeypatch
) -> None:
    auction = _make_auction()
    mock_db_session.execute.return_value = _mock_scalar_result(auction)

    async def failing_publish(*args, **kwargs):
        raise ConnectionError("broker unreachable")

    monkeypatch.setattr("services.bid_service.publish_event", failing_publish)

    response = await client.post(f"/api/v1/auctions/{auction.id}/bids", json={"amount": "15000"})

    assert response.status_code == 503
