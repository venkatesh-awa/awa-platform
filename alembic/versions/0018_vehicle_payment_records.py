"""create and seed vehicle_payment_records for the "Vehicle Pending for
Payment (Buyer)" admin report

Revision ID: 0018_vehicle_payment_records
Revises: 0017_vehicle_status_metrics
Create Date: 2026-07-04

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa

from alembic import op

revision: str = "0018_vehicle_payment_records"
down_revision: str | None = "0017_vehicle_status_metrics"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# (lot_no, chassis_number, title, year_of_make, buyer_name, buyer_email,
#  seller_name, seller_email, payment_status, payment_due_date, location, max_bid)
_RECORDS: list[tuple] = [
    ("100288", "021225191836429", "Buick Other 2019", 2019, "S V Krishna Reddy", "krishnareddy0296@example.com",
     "Rajesh Meesarapu", "dhanasri0911@example.com", "pending_buyer_payment", date(2026, 6, 24), "Dubai", "3900.00"),
    ("100312", "CV888788888", "Bufori Other 2017", 2017, "S V Krishna Reddy", "krishnareddy0296@example.com",
     "Ahmed Abd elnaeim Elmenayar", "sellertestaccount@example.com", "pending_buyer_payment", date(2026, 6, 20),
     "Abu Dhabi - Industrial City", "8100.00"),
    ("100313", "DSFDFGGGGDTTT", "Bentley Continental GT 2018", 2018, "S V Krishna Reddy",
     "krishnareddy0296@example.com", "Ahmed Abd elnaeim Elmenayar", "sellertestaccount@example.com",
     "pending_buyer_payment", date(2026, 6, 20), "Abu Dhabi - Industrial City", "3900.00"),
    ("100314", "CHSN30102025001", "Toyota Fortuner 2021", 2021, "S V Krishna Reddy", "krishnareddy0296@example.com",
     "Rajesh Meesarapu", "dhanasri0911@example.com", "pending_buyer_payment", date(2026, 7, 5), "Abu Dhabi",
     "50000.00"),
    ("100325", "CHSN24022025004", "Mitsubishi XPander 2020", 2020, "S V Krishna Reddy",
     "krishnareddy0296@example.com", "Ahmed Abd elnaeim Elmenayar", "sellertestaccount@example.com",
     "paid_awaiting_documents", None, "Abu Dhabi - Mussaffah Industrial Area", "9700.00"),
    ("100357", "130326144124749", "Toyota Corona 2025", 2025, "S V Krishna Reddy", "krishnareddy0296@example.com",
     "Rajesh Meesarapu", "dhanasri0911@example.com", "pending_buyer_payment", date(2026, 6, 24), "Abu Dhabi",
     "2200.00"),
    ("101131", "130326150434031", "Toyota Fortuner 2020", 2020, "Krishna Reddy11", "sheelamvenkatakrishna@example.com",
     "Krishna Reddy S V33", "udayasheelam81088@example.com", "paid_documents_ready_pending_deliver", None,
     "Abu Dhabi", "34500.00"),
    ("101427", "070426113119568", "Toyota Corona 2021", 2021, "Shishir Patel Buyer", "shishirpatelbuyer@example.com",
     "Rajesh Meesarapu", "dhanasri0911@example.com", "pending_buyer_payment", date(2026, 7, 4), "Abu Dhabi",
     "1500.00"),
    ("101429", "070426113124640", "Toyota Land Cruiser 2025", 2025, "S V Krishna Reddy",
     "krishnareddy0296@example.com", "Rajesh Meesarapu", "dhanasri0911@example.com",
     "paid_documents_ready_pending_deliver", None, "Abu Dhabi", "95000.00"),
    ("101447", "070426113205416", "Nissan Altima 2025", 2025, "S V Krishna Reddy", "krishnareddy0296@example.com",
     "Rajesh Meesarapu", "dhanasri0911@example.com", "pending_buyer_payment", date(2026, 7, 2), "Abu Dhabi",
     "10000.00"),
    ("101448", "070426113207341", "Nissan Sunny 2024", 2024, "S V Krishna Reddy", "krishnareddy0296@example.com",
     "Rajesh Meesarapu", "dhanasri0911@example.com", "pending_buyer_payment", date(2026, 7, 5), "Abu Dhabi",
     "12450.00"),
    ("101454", "070426113240873", "Nissan Altima 2023", 2023, "buyertestuser", "testuseruat@example.com",
     "Krishna Reddy S V", "udayasheelam8108@example.com", "paid_awaiting_documents", None, "Abu Dhabi", "1000.00"),
    ("103147", "CHSN10052025003", "Toyota Camry 2021", 2021, "testdoc", "testdoc@example.com",
     "Krishna Reddy S V", "udayasheelam8108@example.com", "paid_awaiting_documents", None,
     "Abu Dhabi - Al Faya ET Station", "2300.00"),
    ("103148", "CHSN11052026001", "Toyota Land Cruiser 2025", 2025, "S V Krishna Reddy",
     "krishnareddy0296@example.com", "Krishna Reddy S V", "udayasheelam8108@example.com",
     "paid_documents_ready_pending_deliver", None, "Sharjah", "1200.00"),
    ("103153", "123456789001", "Acura CSXEL 2025", 2025, "S V Krishna Reddy", "krishnareddy0296@example.com",
     "Krishna Reddy S V", "udayasheelam8108@example.com", "pending_buyer_payment", date(2026, 6, 7), "Abu Dhabi",
     "200.00"),
    ("103161", "CHSN22052025001", "Toyota Land Cruiser 2021", 2021, "S V Krishna Reddy",
     "krishnareddy0296@example.com", "Krishna Reddy S V", "udayasheelam8108@example.com",
     "paid_documents_ready_pending_deliver", None, "Abu Dhabi", "3100.00"),
    ("103183", "CHSN18062025001", "Toyota Land Cruiser 2021", 2021, "S V Krishna Reddy",
     "krishnareddy0296@example.com", "Krishna Reddy S V", "udayasheelam8108@example.com", "paid_awaiting_documents",
     None, "Abu Dhabi", "10300.00"),
    ("103186", "CHSN22062025001", "Toyota Land Cruiser 5.7 2020", 2020, "testdoc", "testdoc@example.com",
     "Krishna Reddy S V", "udayasheelam8108@example.com", "pending_buyer_payment", date(2026, 7, 4),
     "Abu Dhabi - Al Ajban", "1400.00"),
    ("103187", "CHSN22062026002", "Toyota Fortuner 2025", 2025, "S V Krishna Reddy",
     "krishnareddy0296@example.com", "Anuritha Seller", "anuritha.j@example.com", "pending_buyer_payment",
     date(2026, 6, 28), "Abu Dhabi - Al Ajban", "4400.00"),
    ("100999", "CHSN01012026099", "Nissan Patrol 2024", 2024, "Mohammed Al Zaabi", "mohammed.z@example.com",
     "Fatima Al Nuaimi", "fatima.n@example.com", "pending_seller_payment", date(2026, 6, 30), "Dubai", "42000.00"),
]


def upgrade() -> None:
    op.create_table(
        "vehicle_payment_records",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("lot_no", sa.String(length=50), nullable=False, index=True),
        sa.Column("chassis_number", sa.String(length=100), nullable=False, index=True),
        sa.Column("title", sa.Unicode(length=200), nullable=False),
        sa.Column("year_of_make", sa.Integer(), nullable=False),
        sa.Column("buyer_name", sa.Unicode(length=150), nullable=False, index=True),
        sa.Column("buyer_email", sa.String(length=200), nullable=False),
        sa.Column("seller_name", sa.Unicode(length=150), nullable=False, index=True),
        sa.Column("seller_email", sa.String(length=200), nullable=False),
        sa.Column("payment_status", sa.String(length=50), nullable=False, index=True),
        sa.Column("payment_due_date", sa.Date(), nullable=True),
        sa.Column("location", sa.Unicode(length=200), nullable=False),
        sa.Column("max_bid", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    records = sa.table(
        "vehicle_payment_records",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("lot_no", sa.String(length=50)),
        sa.column("chassis_number", sa.String(length=100)),
        sa.column("title", sa.Unicode(length=200)),
        sa.column("year_of_make", sa.Integer()),
        sa.column("buyer_name", sa.Unicode(length=150)),
        sa.column("buyer_email", sa.String(length=200)),
        sa.column("seller_name", sa.Unicode(length=150)),
        sa.column("seller_email", sa.String(length=200)),
        sa.column("payment_status", sa.String(length=50)),
        sa.column("payment_due_date", sa.Date()),
        sa.column("location", sa.Unicode(length=200)),
        sa.column("max_bid", sa.Numeric(12, 2)),
    )

    op.bulk_insert(
        records,
        [
            {
                "id": _uuid(),
                "lot_no": lot_no,
                "chassis_number": chassis_number,
                "title": title,
                "year_of_make": year_of_make,
                "buyer_name": buyer_name,
                "buyer_email": buyer_email,
                "seller_name": seller_name,
                "seller_email": seller_email,
                "payment_status": payment_status,
                "payment_due_date": payment_due_date,
                "location": location,
                "max_bid": max_bid,
            }
            for (
                lot_no, chassis_number, title, year_of_make, buyer_name, buyer_email,
                seller_name, seller_email, payment_status, payment_due_date, location, max_bid,
            ) in _RECORDS
        ],
    )


def downgrade() -> None:
    op.drop_table("vehicle_payment_records")
