"""Read/write operations backing the seller "Add a New Car" form: static
lookup dropdowns, client/sub-seller user search, and submission create plus
the Mulkhiya document upload.
"""

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.content import VehicleListing
from models.role import Role
from models.sub_seller import SubSeller
from models.user import User
from models.vehicle_intake import (
    BiddingModel,
    FuelType,
    VehicleBranch,
    VehicleColor,
    VehicleKeyOption,
    VehicleMake,
    VehicleModel,
    VehicleYear,
)
from schemas.vehicle_intake import (
    LookupOptionRead,
    SubSellerRead,
    UserLookupRead,
    VehicleBulkRowInput,
    VehicleBulkRowResult,
    VehicleSubmissionCreate,
)
from services.exceptions import DuplicateChassisNumberError, VehicleLookupNotFoundError

Lang = Literal["en", "ar"]


def _pick(en: str, ar: str, lang: Lang) -> str:
    return ar if lang == "ar" and ar else en


async def _active_lookup_options(db: AsyncSession, model: type, lang: Lang) -> list[LookupOptionRead]:
    result = await db.execute(select(model).where(model.is_active).order_by(model.sort_order))
    return [
        LookupOptionRead(id=row.id, label=_pick(row.name_en, row.name_ar, lang), sort_order=row.sort_order)
        for row in result.scalars().all()
    ]


async def get_makes(db: AsyncSession, lang: Lang) -> list[LookupOptionRead]:
    return await _active_lookup_options(db, VehicleMake, lang)


async def get_models(db: AsyncSession, lang: Lang, make_id: uuid.UUID) -> list[LookupOptionRead]:
    result = await db.execute(
        select(VehicleModel)
        .where(VehicleModel.is_active, VehicleModel.make_id == make_id)
        .order_by(VehicleModel.sort_order)
    )
    return [
        LookupOptionRead(id=row.id, label=_pick(row.name_en, row.name_ar, lang), sort_order=row.sort_order)
        for row in result.scalars().all()
    ]


async def get_branches(db: AsyncSession, lang: Lang) -> list[LookupOptionRead]:
    return await _active_lookup_options(db, VehicleBranch, lang)


async def get_colors(db: AsyncSession, lang: Lang) -> list[LookupOptionRead]:
    return await _active_lookup_options(db, VehicleColor, lang)


async def get_key_options(db: AsyncSession, lang: Lang) -> list[LookupOptionRead]:
    return await _active_lookup_options(db, VehicleKeyOption, lang)


async def get_fuel_types(db: AsyncSession, lang: Lang) -> list[LookupOptionRead]:
    return await _active_lookup_options(db, FuelType, lang)


async def get_bidding_models(db: AsyncSession, lang: Lang) -> list[LookupOptionRead]:
    return await _active_lookup_options(db, BiddingModel, lang)


async def get_years(db: AsyncSession) -> list[int]:
    result = await db.execute(
        select(VehicleYear.year).where(VehicleYear.is_active).order_by(VehicleYear.sort_order)
    )
    return list(result.scalars().all())


async def search_clients(db: AsyncSession, q: str) -> list[UserLookupRead]:
    """Clients are sellers (users whose primary role is "Seller")."""
    query = (
        select(User)
        .join(Role, User.primary_role_id == Role.id)
        .where(User.is_active, Role.name == "Seller")
    )
    if q:
        like = f"%{q}%"
        query = query.where(
            or_(User.first_name.ilike(like), User.last_name.ilike(like), User.email.ilike(like))
        )
    result = await db.execute(query.order_by(User.first_name).limit(20))
    return [
        UserLookupRead(id=row.id, name=f"{row.first_name} {row.last_name}".strip(), email=row.email)
        for row in result.scalars().all()
    ]


async def search_sub_sellers(db: AsyncSession, client_id: uuid.UUID, q: str) -> list[SubSellerRead]:
    """Scoped to whichever Client is selected - a sub-seller is a named
    contact under a specific seller, not searchable independently."""
    query = select(SubSeller).where(SubSeller.is_active, SubSeller.seller_id == client_id)
    if q:
        query = query.where(SubSeller.name.ilike(f"%{q}%"))
    result = await db.execute(query.order_by(SubSeller.name).limit(20))
    return [SubSellerRead.model_validate(row) for row in result.scalars().all()]


async def _get_active(db: AsyncSession, model: type, value_id: uuid.UUID):
    result = await db.execute(select(model).where(model.id == value_id, model.is_active))
    return result.scalar_one_or_none()


async def _lookup_exists(db: AsyncSession, model: type, value_id: uuid.UUID) -> bool:
    return await _get_active(db, model, value_id) is not None


async def _user_exists(db: AsyncSession, user_id: uuid.UUID) -> bool:
    result = await db.execute(select(User.id).where(User.id == user_id, User.is_active))
    return result.scalar_one_or_none() is not None


async def _is_sub_seller_of_client(db: AsyncSession, sub_seller_id: uuid.UUID, client_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(SubSeller.id).where(
            SubSeller.id == sub_seller_id, SubSeller.is_active, SubSeller.seller_id == client_id
        )
    )
    return result.scalar_one_or_none() is not None


async def create_vehicle_submission(
    db: AsyncSession, payload: VehicleSubmissionCreate, created_by_id: uuid.UUID
) -> VehicleListing:
    make = await _get_active(db, VehicleMake, payload.make_id)
    if make is None:
        raise VehicleLookupNotFoundError("make_id", payload.make_id)
    model = await _get_active(db, VehicleModel, payload.model_id)
    if model is None:
        raise VehicleLookupNotFoundError("model_id", payload.model_id)
    branch = await _get_active(db, VehicleBranch, payload.branch_id)
    if branch is None:
        raise VehicleLookupNotFoundError("branch_id", payload.branch_id)
    for field, lookup_model, value in [
        ("color_id", VehicleColor, payload.color_id),
        ("keys_option_id", VehicleKeyOption, payload.keys_option_id),
        ("fuel_type_id", FuelType, payload.fuel_type_id),
    ]:
        if not await _lookup_exists(db, lookup_model, value):
            raise VehicleLookupNotFoundError(field, value)
    if payload.bidding_model_id is not None and not await _lookup_exists(
        db, BiddingModel, payload.bidding_model_id
    ):
        raise VehicleLookupNotFoundError("bidding_model_id", payload.bidding_model_id)
    if not await _user_exists(db, payload.client_id):
        raise VehicleLookupNotFoundError("client_id", payload.client_id)
    if payload.sub_seller_id is not None and not await _is_sub_seller_of_client(
        db, payload.sub_seller_id, payload.client_id
    ):
        raise VehicleLookupNotFoundError("sub_seller_id", payload.sub_seller_id)

    listing_id = uuid.uuid4()
    listing = VehicleListing(
        id=listing_id,
        status="submitted",
        is_active=False,
        chassis_number=payload.chassis_number.strip(),
        title_en=f"{make.name_en} {model.name_en} {payload.year}",
        title_ar=f"{make.name_ar} {model.name_ar} {payload.year}",
        detail_url=f"/admin/sellers/vehicle/{listing_id}",
        location_en=branch.name_en,
        location_ar=branch.name_ar,
        make_id=payload.make_id,
        model_id=payload.model_id,
        branch_id=payload.branch_id,
        color_id=payload.color_id,
        keys_option_id=payload.keys_option_id,
        fuel_type_id=payload.fuel_type_id,
        bidding_model_id=payload.bidding_model_id,
        year=payload.year,
        target_selling_price=payload.target_selling_price,
        minimum_selling_price=payload.minimum_selling_price,
        previous_number_plate=payload.previous_number_plate.strip(),
        seller_id=payload.client_id,
        sub_seller_id=payload.sub_seller_id,
        created_by_id=created_by_id,
        mulkhiya_document_url=payload.mulkhiya_document_url,
        terms_accepted=payload.terms_accepted,
    )
    db.add(listing)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DuplicateChassisNumberError(payload.chassis_number) from exc
    await db.refresh(listing)
    return listing


async def _find_lookup_by_label(db: AsyncSession, model: type, label: str, *, make_id: uuid.UUID | None = None):
    """Resolve a bulk-upload cell (typed in English or Arabic) to a lookup
    row. Case-insensitive exact match on either language column - the sheet
    is meant to be filled from the same dropdown values the single-car form
    shows, not free text."""
    query = select(model).where(
        model.is_active,
        or_(func.lower(model.name_en) == label.lower(), func.lower(model.name_ar) == label.lower()),
    )
    if make_id is not None:
        query = query.where(model.make_id == make_id)
    result = await db.execute(query)
    return result.scalars().first()


async def _find_client_by_name(db: AsyncSession, name: str) -> User | None:
    """Clients are sellers (users whose primary role is "Seller"), matched by
    full name or email - mirrors search_clients' matching but expects an
    exact cell value rather than a partial search-as-you-type query."""
    result = await db.execute(
        select(User)
        .join(Role, User.primary_role_id == Role.id)
        .where(
            User.is_active,
            Role.name == "Seller",
            or_(
                func.lower(func.concat(User.first_name, " ", User.last_name)) == name.lower(),
                func.lower(User.email) == name.lower(),
            ),
        )
    )
    return result.scalars().first()


async def _find_sub_seller_by_name(db: AsyncSession, client_id: uuid.UUID, name: str) -> SubSeller | None:
    result = await db.execute(
        select(SubSeller).where(
            SubSeller.is_active, SubSeller.seller_id == client_id, func.lower(SubSeller.name) == name.lower()
        )
    )
    return result.scalars().first()


def _parse_decimal(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.strip())
    except (InvalidOperation, AttributeError):
        return None


def _parse_year(raw: str) -> int | None:
    try:
        return int(raw.strip())
    except (ValueError, AttributeError):
        return None


async def _create_bulk_row(
    db: AsyncSession, row: VehicleBulkRowInput, created_by_id: uuid.UUID
) -> VehicleBulkRowResult:
    errors: dict[str, str] = {}

    if not row.chassis_number.strip():
        errors["chassis_number"] = "Required"
    if not row.previous_number_plate.strip():
        errors["previous_number_plate"] = "Required"

    make = await _find_lookup_by_label(db, VehicleMake, row.make) if row.make.strip() else None
    if make is None:
        errors["make"] = f"Unknown make: {row.make}"

    model = None
    if row.model.strip():
        if make is not None:
            model = await _find_lookup_by_label(db, VehicleModel, row.model, make_id=make.id)
            if model is None:
                errors["model"] = f"Unknown model for {row.make}: {row.model}"
        else:
            errors["model"] = f"Unknown model: {row.model}"
    else:
        errors["model"] = "Required"

    branch = await _find_lookup_by_label(db, VehicleBranch, row.branch) if row.branch.strip() else None
    if branch is None:
        errors["branch"] = f"Unknown branch: {row.branch}"

    color = await _find_lookup_by_label(db, VehicleColor, row.color) if row.color.strip() else None
    if color is None:
        errors["color"] = f"Unknown color: {row.color}"

    keys_option = (
        await _find_lookup_by_label(db, VehicleKeyOption, row.keys_option) if row.keys_option.strip() else None
    )
    if keys_option is None:
        errors["keys_option"] = f"Unknown keys option: {row.keys_option}"

    fuel_type = await _find_lookup_by_label(db, FuelType, row.fuel_type) if row.fuel_type.strip() else None
    if fuel_type is None:
        errors["fuel_type"] = f"Unknown fuel type: {row.fuel_type}"

    bidding_model = None
    if row.bidding_model.strip():
        bidding_model = await _find_lookup_by_label(db, BiddingModel, row.bidding_model)
        if bidding_model is None:
            errors["bidding_model"] = f"Unknown bidding model: {row.bidding_model}"

    year = _parse_year(row.year)
    if year is None:
        errors["year"] = f"Invalid year: {row.year}"

    target_price = _parse_decimal(row.target_selling_price)
    if target_price is None:
        errors["target_selling_price"] = f"Invalid amount: {row.target_selling_price}"

    min_price = _parse_decimal(row.minimum_selling_price)
    if min_price is None:
        errors["minimum_selling_price"] = f"Invalid amount: {row.minimum_selling_price}"

    client = await _find_client_by_name(db, row.client) if row.client.strip() else None
    if client is None:
        errors["client"] = f"Unknown client: {row.client}"

    sub_seller = None
    if row.sub_client.strip() and client is not None:
        sub_seller = await _find_sub_seller_by_name(db, client.id, row.sub_client)
        if sub_seller is None:
            errors["sub_client"] = f"Unknown sub client for {row.client}: {row.sub_client}"

    if errors:
        return VehicleBulkRowResult(
            row_number=row.row_number, status="error", chassis_number=row.chassis_number or None, errors=errors
        )

    assert make and model and branch and color and keys_option and fuel_type and client and year is not None
    listing_id = uuid.uuid4()
    listing = VehicleListing(
        id=listing_id,
        status="submitted",
        is_active=False,
        chassis_number=row.chassis_number.strip(),
        title_en=f"{make.name_en} {model.name_en} {year}",
        title_ar=f"{make.name_ar} {model.name_ar} {year}",
        detail_url=f"/admin/sellers/vehicle/{listing_id}",
        location_en=branch.name_en,
        location_ar=branch.name_ar,
        make_id=make.id,
        model_id=model.id,
        branch_id=branch.id,
        color_id=color.id,
        keys_option_id=keys_option.id,
        fuel_type_id=fuel_type.id,
        bidding_model_id=bidding_model.id if bidding_model else None,
        year=year,
        target_selling_price=target_price,
        minimum_selling_price=min_price,
        previous_number_plate=row.previous_number_plate.strip(),
        seller_id=client.id,
        sub_seller_id=sub_seller.id if sub_seller else None,
        created_by_id=created_by_id,
        mulkhiya_document_url=None,
        terms_accepted=True,
    )
    db.add(listing)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return VehicleBulkRowResult(
            row_number=row.row_number,
            status="error",
            chassis_number=row.chassis_number or None,
            errors={"chassis_number": f"Chassis number already submitted: {row.chassis_number}"},
        )
    return VehicleBulkRowResult(
        row_number=row.row_number,
        status="created",
        chassis_number=listing.chassis_number,
        vehicle_id=listing_id,
    )


async def bulk_create_vehicle_submissions(
    db: AsyncSession, rows: list[VehicleBulkRowInput], created_by_id: uuid.UUID
) -> list[VehicleBulkRowResult]:
    """Processes each row independently so one bad row (unknown lookup,
    duplicate chassis number) doesn't roll back the rows around it - each row
    gets its own commit/rollback."""
    return [await _create_bulk_row(db, row, created_by_id) for row in rows]


_ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


async def save_mulkhiya_document(file: UploadFile) -> str:
    settings = get_settings()

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_DOCUMENT_EXTENSIONS:
        suffix = ".pdf"

    target_dir = Path(settings.upload_dir) / "mulkhiya"
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}{suffix}"
    target_path = target_dir / filename

    contents = await file.read()
    target_path.write_bytes(contents)

    return f"{settings.upload_base_url}/mulkhiya/{filename}"
