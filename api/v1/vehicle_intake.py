"""Seller "Add a New Car" form endpoints: static lookup dropdowns
(unauthenticated, matching api/v1/admin.py's nav/card endpoints - reference
data, not seller data), plus client/sub-seller search and the create +
document-upload endpoints (authenticated - these write data attributed to
the submitting user).
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_local_user, get_db_session
from models.user import User
from schemas.vehicle_intake import (
    DocumentUploadRead,
    LookupOptionRead,
    SubSellerRead,
    UserLookupRead,
    VehicleBulkSubmitRequest,
    VehicleBulkSubmitResult,
    VehicleSubmissionCreate,
    VehicleSubmissionRead,
)
from services import vehicle_intake_service
from services.exceptions import DuplicateChassisNumberError, VehicleLookupNotFoundError

router = APIRouter(prefix="/vehicle-intake", tags=["vehicle-intake"])

LangQuery = Literal["en", "ar"]


@router.get("/makes", response_model=list[LookupOptionRead])
async def get_makes(
    lang: LangQuery = Query(default="en"), db: AsyncSession = Depends(get_db_session)
) -> list[LookupOptionRead]:
    return await vehicle_intake_service.get_makes(db, lang)


@router.get("/models", response_model=list[LookupOptionRead])
async def get_models(
    make_id: uuid.UUID = Query(...),
    lang: LangQuery = Query(default="en"),
    db: AsyncSession = Depends(get_db_session),
) -> list[LookupOptionRead]:
    return await vehicle_intake_service.get_models(db, lang, make_id)


@router.get("/years", response_model=list[int])
async def get_years(db: AsyncSession = Depends(get_db_session)) -> list[int]:
    return await vehicle_intake_service.get_years(db)


@router.get("/branches", response_model=list[LookupOptionRead])
async def get_branches(
    lang: LangQuery = Query(default="en"), db: AsyncSession = Depends(get_db_session)
) -> list[LookupOptionRead]:
    return await vehicle_intake_service.get_branches(db, lang)


@router.get("/colors", response_model=list[LookupOptionRead])
async def get_colors(
    lang: LangQuery = Query(default="en"), db: AsyncSession = Depends(get_db_session)
) -> list[LookupOptionRead]:
    return await vehicle_intake_service.get_colors(db, lang)


@router.get("/key-options", response_model=list[LookupOptionRead])
async def get_key_options(
    lang: LangQuery = Query(default="en"), db: AsyncSession = Depends(get_db_session)
) -> list[LookupOptionRead]:
    return await vehicle_intake_service.get_key_options(db, lang)


@router.get("/fuel-types", response_model=list[LookupOptionRead])
async def get_fuel_types(
    lang: LangQuery = Query(default="en"), db: AsyncSession = Depends(get_db_session)
) -> list[LookupOptionRead]:
    return await vehicle_intake_service.get_fuel_types(db, lang)


@router.get("/bidding-models", response_model=list[LookupOptionRead])
async def get_bidding_models(
    lang: LangQuery = Query(default="en"), db: AsyncSession = Depends(get_db_session)
) -> list[LookupOptionRead]:
    return await vehicle_intake_service.get_bidding_models(db, lang)


@router.get("/clients", response_model=list[UserLookupRead])
async def search_clients(
    q: str = Query(default=""), db: AsyncSession = Depends(get_db_session)
) -> list[UserLookupRead]:
    return await vehicle_intake_service.search_clients(db, q)


@router.get("/sub-sellers", response_model=list[SubSellerRead])
async def search_sub_sellers(
    client_id: uuid.UUID = Query(...),
    q: str = Query(default=""),
    db: AsyncSession = Depends(get_db_session),
) -> list[SubSellerRead]:
    return await vehicle_intake_service.search_sub_sellers(db, client_id, q)


@router.post("/documents", response_model=DocumentUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_mulkhiya_document(
    file: UploadFile,
    user: User = Depends(get_current_local_user),
) -> DocumentUploadRead:
    url = await vehicle_intake_service.save_mulkhiya_document(file)
    return DocumentUploadRead(url=url)


@router.post("/vehicles", response_model=VehicleSubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleSubmissionCreate,
    user: User = Depends(get_current_local_user),
    db: AsyncSession = Depends(get_db_session),
) -> VehicleSubmissionRead:
    try:
        submission = await vehicle_intake_service.create_vehicle_submission(db, payload, user.id)
    except VehicleLookupNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid {exc.field}: {exc.value}"
        ) from exc
    except DuplicateChassisNumberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chassis number already submitted: {exc.chassis_number}",
        ) from exc
    return VehicleSubmissionRead.model_validate(submission)


@router.post("/vehicles/bulk", response_model=VehicleBulkSubmitResult, status_code=status.HTTP_200_OK)
async def create_vehicles_bulk(
    payload: VehicleBulkSubmitRequest,
    user: User = Depends(get_current_local_user),
    db: AsyncSession = Depends(get_db_session),
) -> VehicleBulkSubmitResult:
    """"Sell Multiple Cars" bulk upload - each row is validated and created
    independently, so partial success (some rows created, others rejected)
    is a 200 response with per-row results rather than an all-or-nothing
    transaction."""
    results = await vehicle_intake_service.bulk_create_vehicle_submissions(db, payload.rows, user.id)
    created_count = sum(1 for r in results if r.status == "created")
    return VehicleBulkSubmitResult(
        total=len(results),
        created_count=created_count,
        error_count=len(results) - created_count,
        results=results,
    )
