"""Vehicle payment-status reporting: one row per vehicle currently moving
through the post-auction buyer/seller payment and document-handover flow.

Deliberately denormalized (buyer/seller name+email, title, location stored
directly on the row) rather than joined through VehicleListing/User, mirroring
the flattened shape the admin "Vehicle Pending for Payment (Buyer)" report
already expects and keeping this reporting table decoupled from the core
auction domain.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, Unicode, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class VehiclePaymentRecord(Base):
    __tablename__ = "vehicle_payment_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    chassis_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    year_of_make: Mapped[int] = mapped_column(nullable=False)
    buyer_name: Mapped[str] = mapped_column(Unicode(150), nullable=False, index=True)
    buyer_email: Mapped[str] = mapped_column(String(200), nullable=False)
    seller_name: Mapped[str] = mapped_column(Unicode(150), nullable=False, index=True)
    seller_email: Mapped[str] = mapped_column(String(200), nullable=False)
    # One of the vehicle_status_metrics(group_key="payment_summary").stat_key
    # values - "paid_awaiting_documents", "paid_documents_ready_pending_deliver",
    # "pending_buyer_payment", "pending_seller_payment".
    payment_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payment_due_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    location: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    max_bid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
