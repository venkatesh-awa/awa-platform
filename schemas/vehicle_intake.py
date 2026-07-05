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
