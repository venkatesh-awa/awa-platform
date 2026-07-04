"""Response schemas for the vehicle payment-status report (the "Vehicle
Pending for Payment (Buyer)" admin dashboard)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class VehiclePaymentRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lot_no: str
    chassis_number: str
    title: str
    year_of_make: int
    buyer_name: str
    buyer_email: str
    seller_name: str
    seller_email: str
    payment_status: str
    payment_due_date: date | None
    location: str
    max_bid: Decimal


class VehiclePaymentRecordPage(BaseModel):
    records: list[VehiclePaymentRecordRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class VehiclePaymentStatusCounts(BaseModel):
    paid_awaiting_documents: int
    paid_documents_ready_pending_deliver: int
    pending_buyer_payment: int
    pending_seller_payment: int
