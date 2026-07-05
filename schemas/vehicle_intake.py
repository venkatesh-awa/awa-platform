"""Request/response schemas for the seller "Add a New Car" form: lookup
dropdown options, client/sub-seller search results, and the submission
create/read shapes."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LookupOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    sort_order: int = 0


class YearOptionRead(BaseModel):
    year: int


class UserLookupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str


class SubSellerRead(BaseModel):
    """A client's named contact - no email/login, unlike UserLookupRead."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    phone: str | None


class VehicleSubmissionCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    chassis_number: str = Field(min_length=1, max_length=100)
    make_id: uuid.UUID
    model_id: uuid.UUID
    branch_id: uuid.UUID
    color_id: uuid.UUID
    keys_option_id: uuid.UUID
    fuel_type_id: uuid.UUID
    bidding_model_id: uuid.UUID | None = None
    year: int
    target_selling_price: Decimal
    minimum_selling_price: Decimal
    previous_number_plate: str = Field(min_length=1, max_length=50)
    client_id: uuid.UUID
    sub_seller_id: uuid.UUID | None = None
    mulkhiya_document_url: str | None = None
    terms_accepted: bool


class VehicleSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chassis_number: str
    status: str
    created_at: datetime


class DocumentUploadRead(BaseModel):
    url: str


class VehicleBulkRowInput(BaseModel):
    """One row of the "Sell Multiple Cars" bulk upload sheet. Every lookup is
    a human-readable label (English or Arabic, as typed into the sheet) - the
    service layer resolves labels to ids, unlike VehicleSubmissionCreate which
    already has resolved ids from the single-car form's dropdowns."""

    model_config = ConfigDict(protected_namespaces=())

    row_number: int
    chassis_number: str = ""
    make: str = ""
    model: str = ""
    branch: str = ""
    year: str = ""
    keys_option: str = ""
    fuel_type: str = ""
    color: str = ""
    target_selling_price: str = ""
    minimum_selling_price: str = ""
    client: str = ""
    sub_client: str = ""
    previous_number_plate: str = ""
    bidding_model: str = ""


class VehicleBulkSubmitRequest(BaseModel):
    rows: list[VehicleBulkRowInput] = Field(min_length=1, max_length=500)


class VehicleBulkRowResult(BaseModel):
    row_number: int
    status: str  # "created" | "error"
    chassis_number: str | None = None
    vehicle_id: uuid.UUID | None = None
    errors: dict[str, str] | None = None


class VehicleBulkSubmitResult(BaseModel):
    total: int
    created_count: int
    error_count: int
    results: list[VehicleBulkRowResult]
