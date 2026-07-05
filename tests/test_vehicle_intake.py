from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from models.sub_seller import SubSeller
from models.vehicle_intake import VehicleMake


def _mock_scalars_result(items: list) -> MagicMock:
    scalars = MagicMock()
    scalars.all.return_value = items
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalars_first_result(value) -> MagicMock:
    scalars = MagicMock()
    scalars.first.return_value = value
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


def _make(name_en: str, name_ar: str, sort_order: int = 1) -> VehicleMake:
    return VehicleMake(id=uuid.uuid4(), name_en=name_en, name_ar=name_ar, sort_order=sort_order, is_active=True)


def _bulk_row(**overrides) -> dict:
    row = {
        "row_number": 1,
        "chassis_number": "CHSN99999",
        "make": "Toyota",
        "model": "Camry",
        "branch": "Abu Dhabi",
        "year": "2022",
        "keys_option": "1 Key",
        "fuel_type": "Petrol",
        "color": "White",
        "target_selling_price": "50000",
        "minimum_selling_price": "40000",
        "client": "Seller One",
        "sub_client": "",
        "previous_number_plate": "A12345",
        "bidding_model": "",
    }
    row.update(overrides)
    return row


def _submission_payload(**overrides) -> dict:
    payload = {
        "chassis_number": "CHSN12345",
        "make_id": str(uuid.uuid4()),
        "model_id": str(uuid.uuid4()),
        "branch_id": str(uuid.uuid4()),
        "color_id": str(uuid.uuid4()),
        "keys_option_id": str(uuid.uuid4()),
        "fuel_type_id": str(uuid.uuid4()),
        "bidding_model_id": None,
        "year": 2022,
        "target_selling_price": "50000.00",
        "minimum_selling_price": "40000.00",
        "previous_number_plate": "A12345",
        "client_id": str(uuid.uuid4()),
        "sub_seller_id": None,
        "mulkhiya_document_url": None,
        "terms_accepted": True,
    }
    payload.update(overrides)
    return payload


async def test_get_makes_returns_english_labels_by_default(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result([_make("Toyota", "تويوتا")])

    response = await client.get("/api/v1/vehicle-intake/makes")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "Toyota"


async def test_get_makes_returns_arabic_labels_when_requested(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result([_make("Toyota", "تويوتا")])

    response = await client.get("/api/v1/vehicle-intake/makes?lang=ar")

    assert response.status_code == 200
    assert response.json()[0]["label"] == "تويوتا"


async def test_get_models_requires_make_id(client: AsyncClient, mock_db_session: MagicMock) -> None:
    response = await client.get("/api/v1/vehicle-intake/models")

    assert response.status_code == 422


async def test_get_years_returns_seeded_years(client: AsyncClient, mock_db_session: MagicMock) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result([2025, 2024, 1927])

    response = await client.get("/api/v1/vehicle-intake/years")

    assert response.status_code == 200
    assert response.json() == [2025, 2024, 1927]


async def test_create_vehicle_happy_path(client: AsyncClient, mock_db_session: MagicMock) -> None:
    lookup_row = _make("Toyota", "تويوتا")
    mock_db_session.execute.return_value = _mock_scalar_result(lookup_row)

    async def _fake_refresh(instance) -> None:
        instance.created_at = datetime.now(UTC)

    mock_db_session.refresh = AsyncMock(side_effect=_fake_refresh)

    response = await client.post("/api/v1/vehicle-intake/vehicles", json=_submission_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["chassis_number"] == "CHSN12345"
    assert body["status"] == "submitted"


async def test_create_vehicle_rejects_unknown_make(client: AsyncClient, mock_db_session: MagicMock) -> None:
    mock_db_session.execute.return_value = _mock_scalar_result(None)

    response = await client.post("/api/v1/vehicle-intake/vehicles", json=_submission_payload())

    assert response.status_code == 404


async def test_create_vehicle_rejects_duplicate_chassis_number(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalar_result(_make("Toyota", "تويوتا"))
    mock_db_session.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))

    response = await client.post("/api/v1/vehicle-intake/vehicles", json=_submission_payload())

    assert response.status_code == 409


async def test_create_vehicle_requires_auth(
    unauthenticated_client: AsyncClient, mock_db_session: MagicMock
) -> None:
    response = await unauthenticated_client.post(
        "/api/v1/vehicle-intake/vehicles", json=_submission_payload()
    )

    assert response.status_code == 401


async def test_search_sub_sellers_requires_client_id(client: AsyncClient, mock_db_session: MagicMock) -> None:
    response = await client.get("/api/v1/vehicle-intake/sub-sellers")

    assert response.status_code == 422


async def test_search_sub_sellers_scopes_to_client(client: AsyncClient, mock_db_session: MagicMock) -> None:
    mock_db_session.execute.return_value = _mock_scalars_result([])

    response = await client.get(f"/api/v1/vehicle-intake/sub-sellers?client_id={uuid.uuid4()}")

    assert response.status_code == 200
    assert response.json() == []


async def test_search_sub_sellers_returns_name_and_phone(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    sub_seller = SubSeller(
        id=uuid.uuid4(), seller_id=uuid.uuid4(), name="Anuritha 1", phone="+876098123", is_active=True
    )
    mock_db_session.execute.return_value = _mock_scalars_result([sub_seller])

    response = await client.get(f"/api/v1/vehicle-intake/sub-sellers?client_id={uuid.uuid4()}")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["name"] == "Anuritha 1"
    assert body[0]["phone"] == "+876098123"
    assert "email" not in body[0]


async def test_create_vehicle_rejects_sub_seller_not_belonging_to_client(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    make = _make("Toyota", "تويوتا")

    call_count = {"n": 0}

    def _execute_side_effect(*_args, **_kwargs):
        call_count["n"] += 1
        # make/model/branch/color/keys/fuel/client_id checks all pass (6+1
        # execute calls); the final sub_seller-belongs-to-client check fails.
        if call_count["n"] <= 7:
            return _mock_scalar_result(make)
        return _mock_scalar_result(None)

    mock_db_session.execute.side_effect = _execute_side_effect

    response = await client.post(
        "/api/v1/vehicle-intake/vehicles",
        json=_submission_payload(sub_seller_id=str(uuid.uuid4())),
    )

    assert response.status_code == 404
    assert "sub_seller_id" in response.json()["detail"]


def _lookup(name_en: str, name_ar: str = "") -> MagicMock:
    row = MagicMock()
    row.id = uuid.uuid4()
    row.name_en = name_en
    row.name_ar = name_ar or name_en
    return row


async def test_bulk_create_happy_path(client: AsyncClient, mock_db_session: MagicMock) -> None:
    make = _lookup("Toyota", "تويوتا")
    model = _lookup("Camry", "كامري")
    branch = _lookup("Abu Dhabi", "أبو ظبي")
    color = _lookup("White", "أبيض")
    keys_option = _lookup("1 Key", "مفتاح واحد")
    fuel_type = _lookup("Petrol", "بنزين")
    seller_user = MagicMock()
    seller_user.id = uuid.uuid4()

    mock_db_session.execute.side_effect = [
        _mock_scalars_first_result(make),
        _mock_scalars_first_result(model),
        _mock_scalars_first_result(branch),
        _mock_scalars_first_result(color),
        _mock_scalars_first_result(keys_option),
        _mock_scalars_first_result(fuel_type),
        _mock_scalars_first_result(seller_user),
    ]

    response = await client.post(
        "/api/v1/vehicle-intake/vehicles/bulk", json={"rows": [_bulk_row()]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 1
    assert body["error_count"] == 0
    assert body["results"][0]["status"] == "created"
    assert body["results"][0]["chassis_number"] == "CHSN99999"


async def test_bulk_create_reports_row_error_for_unknown_make(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    mock_db_session.execute.return_value = _mock_scalars_first_result(None)

    response = await client.post(
        "/api/v1/vehicle-intake/vehicles/bulk",
        json={"rows": [_bulk_row(make="Not A Real Make")]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 0
    assert body["error_count"] == 1
    assert body["results"][0]["status"] == "error"
    assert "make" in body["results"][0]["errors"]


async def test_bulk_create_rejects_duplicate_chassis_number(
    client: AsyncClient, mock_db_session: MagicMock
) -> None:
    make = _lookup("Toyota", "تويوتا")
    model = _lookup("Camry", "كامري")
    branch = _lookup("Abu Dhabi", "أبو ظبي")
    color = _lookup("White", "أبيض")
    keys_option = _lookup("1 Key", "مفتاح واحد")
    fuel_type = _lookup("Petrol", "بنزين")
    seller_user = MagicMock()
    seller_user.id = uuid.uuid4()

    mock_db_session.execute.side_effect = [
        _mock_scalars_first_result(make),
        _mock_scalars_first_result(model),
        _mock_scalars_first_result(branch),
        _mock_scalars_first_result(color),
        _mock_scalars_first_result(keys_option),
        _mock_scalars_first_result(fuel_type),
        _mock_scalars_first_result(seller_user),
    ]
    mock_db_session.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))

    response = await client.post(
        "/api/v1/vehicle-intake/vehicles/bulk", json={"rows": [_bulk_row()]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["status"] == "error"
    assert "chassis_number" in body["results"][0]["errors"]


async def test_bulk_create_requires_auth(unauthenticated_client: AsyncClient, mock_db_session: MagicMock) -> None:
    response = await unauthenticated_client.post(
        "/api/v1/vehicle-intake/vehicles/bulk", json={"rows": [_bulk_row()]}
    )

    assert response.status_code == 401


async def test_bulk_create_rejects_empty_rows(client: AsyncClient, mock_db_session: MagicMock) -> None:
    response = await client.post("/api/v1/vehicle-intake/vehicles/bulk", json={"rows": []})

    assert response.status_code == 422
