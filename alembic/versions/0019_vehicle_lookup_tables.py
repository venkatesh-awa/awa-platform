"""create and seed the lookup tables backing the seller "Add a New Car" form
(make, model, year, branch, color, key options, fuel type, bidding model).

Seed values for year/branch/color/key options/fuel type/bidding model/make
are taken verbatim from the live Al Wataneya admin module's reference data
(categories, fleet_spec_values, auction_types endpoints) so these dropdowns
match production. Per-make models aren't in that source payload, so only the
makes we could hand-curate real models for carry any models seed row - the
rest are seeded make-only and get model options once real data is available.

Revision ID: 0019_vehicle_lookup_tables
Revises: 0018_vehicle_payment_records
Create Date: 2026-07-05

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019_vehicle_lookup_tables"
down_revision: str | None = "0018_vehicle_payment_records"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _simple_lookup_table(name: str, name_len: int = 100) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name_en", sa.Unicode(length=name_len), nullable=False),
        sa.Column("name_ar", sa.Unicode(length=name_len), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
    )


def _seed(table_name: str, name_len: int, rows: list[tuple[str, str]]) -> None:
    table = sa.table(
        table_name,
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("name_en", sa.Unicode(length=name_len)),
        sa.column("name_ar", sa.Unicode(length=name_len)),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        table,
        [
            {"id": _uuid(), "name_en": name_en, "name_ar": name_ar, "sort_order": sort_order, "is_active": True}
            for sort_order, (name_en, name_ar) in enumerate(rows, start=1)
        ],
    )


# Real branch list (fleet_spec_values.branch) - just the two active yards.
_BRANCHES: list[tuple[str, str]] = [
    ("Abu Dhabi", "أبو ظبي"),
    ("Sharjah", "الشارقة"),
]

# Real color list (fleet_spec_values.color), source didn't localize most of
# these so untranslated entries repeat the English label as the Arabic value,
# same convention the source payload itself uses for un-translated fields.
_COLORS: list[tuple[str, str]] = [
    ("-", "-"),
    ("Beige", "بيج"),
    ("Black", "أسود"),
    ("Blue", "أزرق"),
    ("Brown", "بني"),
    ("Burgundy", "عنابي"),
    ("Dark blue", "أزرق داكن"),
    ("Golden", "ذهبي"),
    ("Gray Color", "Gray Color"),
    ("Green", "أخضر"),
    ("Grey", "رمادي"),
    ("LEADEN", "LEADEN"),
    ("Maroon", "خمري"),
    ("ORANGE", "برتقالي"),
    ("Other Color", "لون آخر"),
    ("pearly white", "أبيض لؤلؤي"),
    ("Pink", "وردي"),
    ("Purple", "بنفسجي"),
    ("Red", "أحمر"),
    ("Silver", "فضي"),
    ("Tan", "Tan"),
    ("Teal", "Teal"),
    ("White", "أبيض"),
    ("White Pink", "White Pink"),
    ("Yellow", "أصفر"),
]

# Key-count options for the "Keys" dropdown. Source system's fleet_spec_values.keys
# has a "0" (no key) option with plain-number labels; product wants that
# dropped and the remaining counts phrased as "1 Key"/"2 Keys"/"3 Keys".
_KEY_OPTIONS: list[tuple[str, str]] = [
    ("1 Key", "مفتاح واحد"),
    ("2 Keys", "مفتاحان"),
    ("3 Keys", "3 مفاتيح"),
]

# Real fuel types (fleet_spec_values.fuel_type) - excludes the source's ".."
# placeholder row, which isn't a meaningful fuel type.
_FUEL_TYPES: list[tuple[str, str]] = [
    ("Petrol", "بنزين"),
    ("Diesel", "ديزل"),
    ("Hybrid", "هجين"),
    ("Electric", "كهربائي"),
    ("CNG", "غاز طبيعي مضغوط"),
]

# Real auction types (biddingModels), Arabic values copied verbatim from the
# source for the ones it already has real translations for.
_BIDDING_MODELS: list[tuple[str, str]] = [
    ("Regular auction", "Regular auction"),
    ("Offline auction", "Offline auction"),
    ("Hybrid auction", "Hybrid auction"),
    ("Silent auction", "المزاد الصامت"),
    ("Direct auction", "العمل المباشر"),
]

# Real year list (fleet_spec_values.year_make) - non-contiguous (skips
# 1959/1955-1957/1949/1951-1953/etc.), so this must be a seeded lookup table
# rather than a computed range.
_YEARS: list[int] = [
    2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010,
    2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994,
    1993, 1992, 1991, 1990, 1989, 1988, 1987, 1986, 1985, 1984, 1983, 1982, 1981, 1980, 1979, 1978,
    1977, 1976, 1975, 1974, 1973, 1972, 1971, 1970, 1969, 1968, 1967, 1966, 1965, 1964, 1963, 1962,
    1961, 1960, 1958, 1954, 1950, 1948, 1927,
]

# Real make list (categories, parent_id "1", cat_id 198-267) - the
# contiguous "standard car make" block; the source category tree continues
# past cat_id 267 into non-car equipment/scrap/test rows which don't belong
# in a car-sell form.
_MAKES: list[str] = [
    "Acura", "Alfa Romeo", "Aston Martin", "Audi", "Bentley", "Bizzarrini", "BMW", "Bufori", "Bugatti",
    "Buick", "Cadillac", "Chevrolet", "Chrysler", "Citroen", "Scrap", "Daewoo", "Daihatsu", "DeLorean",
    "Dodge", "Ferrari", "Fiat", "Ford", "GMC", "Honda", "Hummer", "Hyundai", "Infiniti", "Isuzu",
    "Jaguar", "Jeep", "Kia", "Lada", "Lamborghini", "Lancia", "Land Rover", "Lexus", "Lincoln", "Lotus",
    "Maserati", "Maybach", "Mazda", "McLaren", "Mercedes-Benz", "Mercury", "MINI", "Mitsubishi",
    "Nissan", "Opel", "Oullim", "Peugeot", "Pontiac", "Porsche", "Proton", "Renault", "Rolls Royce",
    "Range Rover", "Saab", "25 Seats", "Skoda", "Smart", "Speranza", "Ssang Yong", "Subaru", "Suzuki",
    "TATA", "Toyota", "Volkswagen", "Volvo", "Wiesmann", "Other Make",
]

# Hand-curated models for the makes we can vouch for real model names on -
# the "Add a New Car" source payload didn't include a per-make model list.
# Every other make above is seeded without models until that data exists.
_MODELS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Toyota": [("Camry", "كامري"), ("Corolla", "كورولا"), ("Land Cruiser", "لاند كروزر"),
               ("Fortuner", "فورتشنر"), ("Hilux", "هايلكس"), ("Yaris", "ياريس")],
    "Nissan": [("Altima", "التيما"), ("Patrol", "باترول"), ("Sunny", "صني"),
               ("X-Trail", "اكس تريل"), ("Maxima", "ماكسيما")],
    "Honda": [("Accord", "أكورد"), ("Civic", "سيفيك"), ("CR-V", "سي آر-في")],
    "Mercedes-Benz": [("C-Class", "الفئة C"), ("E-Class", "الفئة E"), ("S-Class", "الفئة S"),
                       ("GLE", "جي إل إي")],
    "BMW": [("3 Series", "الفئة 3"), ("5 Series", "الفئة 5"), ("X5", "إكس 5")],
    "Ford": [("Explorer", "إكسبلورر"), ("F-150", "إف-150"), ("Mustang", "موستنج")],
    "Chevrolet": [("Tahoe", "تاهو"), ("Malibu", "ماليبو"), ("Camaro", "كامارو")],
    "Hyundai": [("Elantra", "إلنترا"), ("Sonata", "سوناتا"), ("Tucson", "توسان")],
    "Kia": [("Sportage", "سبورتاج"), ("Sorento", "سورينتو"), ("Optima", "أوبتيما")],
    "Lexus": [("ES", "إي إس"), ("RX", "آر إكس"), ("LX", "إل إكس")],
    "Mitsubishi": [("Pajero", "باجيرو"), ("Lancer", "لانسر"), ("Attrage", "أتراج")],
    "Land Rover": [("Range Rover", "رينج روفر"), ("Discovery", "ديسكفري"), ("Defender", "ديفندر")],
    "Audi": [("A4", "إيه 4"), ("A6", "إيه 6"), ("Q7", "كيو 7")],
    "Volkswagen": [("Passat", "باسات"), ("Tiguan", "تيغوان"), ("Golf", "جولف")],
    "Mazda": [("CX-5", "سي إكس-5"), ("Mazda 6", "مازدا 6"), ("Mazda 3", "مازدا 3")],
}


def upgrade() -> None:
    _simple_lookup_table("vehicle_makes")
    op.create_table(
        "vehicle_models",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "make_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("vehicle_makes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name_en", sa.Unicode(length=100), nullable=False),
        sa.Column("name_ar", sa.Unicode(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
    )
    _simple_lookup_table("vehicle_branches")
    _simple_lookup_table("vehicle_colors", name_len=50)
    _simple_lookup_table("vehicle_key_options", name_len=50)
    _simple_lookup_table("fuel_types", name_len=50)
    _simple_lookup_table("bidding_models")
    op.create_table(
        "vehicle_years",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
    )

    _seed("vehicle_branches", 100, _BRANCHES)
    _seed("vehicle_colors", 50, _COLORS)
    _seed("vehicle_key_options", 50, _KEY_OPTIONS)
    _seed("fuel_types", 50, _FUEL_TYPES)
    _seed("bidding_models", 100, _BIDDING_MODELS)

    years_table = sa.table(
        "vehicle_years",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("year", sa.Integer()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        years_table,
        [
            {"id": _uuid(), "year": year, "sort_order": sort_order, "is_active": True}
            for sort_order, year in enumerate(_YEARS, start=1)
        ],
    )

    makes_table = sa.table(
        "vehicle_makes",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("name_en", sa.Unicode(length=100)),
        sa.column("name_ar", sa.Unicode(length=100)),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    models_table = sa.table(
        "vehicle_models",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("make_id", sa.Uuid(as_uuid=True)),
        sa.column("name_en", sa.Unicode(length=100)),
        sa.column("name_ar", sa.Unicode(length=100)),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )

    model_rows = []
    for make_sort, make_en in enumerate(_MAKES, start=1):
        make_id = _uuid()
        op.execute(
            makes_table.insert().values(
                id=make_id, name_en=make_en, name_ar=make_en, sort_order=make_sort, is_active=True
            )
        )
        for model_sort, (model_en, model_ar) in enumerate(_MODELS_BY_MAKE.get(make_en, []), start=1):
            model_rows.append(
                {
                    "id": _uuid(),
                    "make_id": make_id,
                    "name_en": model_en,
                    "name_ar": model_ar,
                    "sort_order": model_sort,
                    "is_active": True,
                }
            )
    if model_rows:
        op.bulk_insert(models_table, model_rows)


def downgrade() -> None:
    op.drop_table("vehicle_years")
    op.drop_table("vehicle_models")
    op.drop_table("vehicle_makes")
    op.drop_table("bidding_models")
    op.drop_table("fuel_types")
    op.drop_table("vehicle_key_options")
    op.drop_table("vehicle_colors")
    op.drop_table("vehicle_branches")
