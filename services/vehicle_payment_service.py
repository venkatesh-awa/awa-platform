"""Read operations for the vehicle payment-status report (the "Vehicle
Pending for Payment (Buyer)" admin dashboard). Unauthenticated for now,
matching the rest of api/v1/admin.py - this only exposes reporting data
already visible on the admin dashboard, no new access surface.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.vehicle_payment import VehiclePaymentRecord
from schemas.vehicle_payment import (
    VehicleInStoreRecordPage,
    VehicleInStoreRecordRead,
    VehiclePaymentRecordPage,
    VehiclePaymentRecordRead,
    VehiclePaymentStatusCounts,
)

_STATUS_KEYS = [
    "paid_awaiting_documents",
    "paid_documents_ready_pending_deliver",
    "pending_buyer_payment",
    "pending_seller_payment",
]

# Column the "In Store" report is allowed to sort by, keyed by the frontend's
# sort_by query value - keeps arbitrary column names out of order_by().
_IN_STORE_SORT_COLUMNS = {
    "id": VehiclePaymentRecord.lot_no,
    "chassis_number": VehiclePaymentRecord.chassis_number,
    "title": VehiclePaymentRecord.title,
    "location": VehiclePaymentRecord.location,
}


async def get_vehicle_payment_status_counts(db: AsyncSession) -> VehiclePaymentStatusCounts:
    result = await db.execute(
        select(VehiclePaymentRecord.payment_status, func.count())
        .group_by(VehiclePaymentRecord.payment_status)
    )
    counts = dict(result.all())
    return VehiclePaymentStatusCounts(**{key: counts.get(key, 0) for key in _STATUS_KEYS})


async def get_vehicle_payment_records(
    db: AsyncSession,
    *,
    status: str,
    lot_no: str = "",
    chassis_number: str = "",
    buyer_name: str = "",
    seller_name: str = "",
    page: int = 1,
    page_size: int = 50,
) -> VehiclePaymentRecordPage:
    query = select(VehiclePaymentRecord)

    if status and status != "ALL":
        query = query.where(VehiclePaymentRecord.payment_status == status)
    if lot_no:
        query = query.where(VehiclePaymentRecord.lot_no.ilike(f"%{lot_no}%"))
    if chassis_number:
        query = query.where(VehiclePaymentRecord.chassis_number.ilike(f"%{chassis_number}%"))
    if buyer_name:
        query = query.where(VehiclePaymentRecord.buyer_name.ilike(f"%{buyer_name}%"))
    if seller_name:
        query = query.where(VehiclePaymentRecord.seller_name.ilike(f"%{seller_name}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    page = max(page, 1)
    page_size = max(min(page_size, 200), 1)
    total_pages = max((total + page_size - 1) // page_size, 1)

    rows = (
        await db.execute(
            query.order_by(VehiclePaymentRecord.lot_no).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()

    return VehiclePaymentRecordPage(
        records=[VehiclePaymentRecordRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_vehicle_in_store_records(
    db: AsyncSession,
    *,
    id_search: str = "",
    chassis_number: str = "",
    seller_name: str = "",
    location: str = "",
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 50,
) -> VehicleInStoreRecordPage:
    """Vehicles currently in the yard, independent of payment status - reuses
    vehicle_payment_records (the closest existing per-vehicle table) rather
    than introducing a parallel inventory table."""
    query = select(VehiclePaymentRecord)

    if id_search:
        query = query.where(VehiclePaymentRecord.lot_no.ilike(f"%{id_search}%"))
    if chassis_number:
        query = query.where(VehiclePaymentRecord.chassis_number.ilike(f"%{chassis_number}%"))
    if seller_name:
        query = query.where(VehiclePaymentRecord.seller_name.ilike(f"%{seller_name}%"))
    if location:
        query = query.where(VehiclePaymentRecord.location.ilike(f"%{location}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    page = max(page, 1)
    page_size = max(min(page_size, 200), 1)
    total_pages = max((total + page_size - 1) // page_size, 1)

    sort_column = _IN_STORE_SORT_COLUMNS.get(sort_by, VehiclePaymentRecord.lot_no)
    order = sort_column.desc() if sort_dir == "desc" else sort_column.asc()

    rows = (
        await db.execute(query.order_by(order).offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return VehicleInStoreRecordPage(
        records=[
            VehicleInStoreRecordRead(
                id=row.lot_no,
                chassis_number=row.chassis_number,
                title=row.title,
                location=row.location,
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
