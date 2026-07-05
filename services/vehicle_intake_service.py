"""Read/write operations backing the seller "Add a New Car" form: static
lookup dropdowns, client/sub-seller user search, and submission create plus
the Mulkhiya document upload.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.content import VehicleListing
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
    UserLookupRead,
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


def _apply_name_filter(query, q: str):
    if not q:
        return query
    like = f"%{q}%"
    return query.where(or_(User.first_name.ilike(like), User.last_name.ilike(like), User.email.ilike(like)))


async def search_clients(db: AsyncSession, q: str) -> list[UserLookupRead]:
    """Clients are top-level sellers - accounts with no parent_seller_id.
    Sub-seller accounts aren't themselves selectable as a Client."""
    query = select(User).where(User.is_active, User.role == "Seller", User.parent_seller_id.is_(None))
    query = _apply_name_filter(query, q)
    result = await db.execute(query.order_by(User.first_name).limit(20))
    return [
        UserLookupRead(id=row.id, name=f"{row.first_name} {row.last_name}".strip(), email=row.email)
        for row in result.scalars().all()
    ]


async def search_sub_sellers(db: AsyncSession, client_id: uuid.UUID, q: str) -> list[UserLookupRead]:
    """Scoped to whichever Client is selected - a sub-seller only exists
    under a specific client, not searchable independently."""
    query = select(User).where(User.is_active, User.role == "Seller", User.parent_seller_id == client_id)
    query = _apply_name_filter(query, q)
    result = await db.execute(query.order_by(User.first_name).limit(20))
    return [
        UserLookupRead(id=row.id, name=f"{row.first_name} {row.last_name}".strip(), email=row.email)
        for row in result.scalars().all()
    ]


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
        select(User.id).where(
            User.id == sub_seller_id, User.is_active, User.parent_seller_id == client_id
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
