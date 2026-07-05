"""roles + user_roles: normalized RBAC replacing the ad hoc users.role string.

Adds:
- `roles`: seeded reference table (Buyer, Seller, Admin, Accountant,
  Inspector, Manager, Operations, AuctionsHead - see rationale below).
- `user_roles`: many-to-many join between users and roles, so a user can
  hold more than one role (e.g. a Seller who also buys). `is_primary` marks
  which assignment is mirrored onto the legacy `users.role` column that
  bid_service.REQUIRED_BID_ROLES, vehicle_intake_service's seller lookups,
  and the JWT `roles` claim (services/auth_service._issue_token_pair)
  already read - kept as-is so this migration ships without touching those
  call sites. A filtered unique index guarantees at most one primary role
  per user at the database level.

Role rationale:
- Buyer / Seller / Admin: already live in users.role today.
- Accountant: matches the existing "Accountant" admin section
  (admin_nav_items.url = '/admin/accountant'; see 0010/0014).
- Inspector: the vehicle-inspection domain already exists (inspection
  packages/invoices/reports, the "Inspection Executive" seed contact in
  0021) but had no role of its own.
- Manager / Operations: match the existing "Management" and "Operations"
  admin sections (0010/0012/0013).
- AuctionsHead: services/bid_service.REQUIRED_BID_ROLES already grants this
  role bidding rights alongside Buyer, but no such role has ever existed in
  users.role - this migration closes that gap.

Backfill: every existing user gets a `user_roles` row for their current
`users.role` value, marked primary. Any legacy role string that doesn't
match a seeded role is preserved as its own additional role row (rather than
silently dropped or collapsed to Buyer), so no user's existing role is lost
and every user ends up with at least one row in `user_roles`.

Revision ID: 0029_roles
Revises: 0028_menu_admin_icon_null
Create Date: 2026-07-05

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0029_roles"
down_revision: str | None = "0028_menu_admin_icon_null"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_SEED_ROLES: list[tuple[str, str]] = [
    ("Buyer", "Bids on and purchases vehicles in auctions."),
    ("Seller", "Lists vehicles for sale/auction."),
    ("Admin", "Full administrative access to the admin dashboard."),
    ("Accountant", "Finance/billing staff - admin Accountant section (invoices, payments)."),
    ("Inspector", "Performs and reports on vehicle inspections."),
    ("Manager", "Admin Management section (penalties, subscriptions, etc.)."),
    ("Operations", "Admin Operations section (inspection service scheduling, operation logs)."),
    ("AuctionsHead", "Elevated bidding rights alongside Buyer - see services/bid_service.REQUIRED_BID_ROLES."),
]


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Unicode(length=50), nullable=False),
        sa.Column("description", sa.Unicode(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("uq_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index(
        "uq_user_roles_user_id_role_id", "user_roles", ["user_id", "role_id"], unique=True
    )
    op.create_index(
        "uq_user_roles_one_primary_per_user",
        "user_roles",
        ["user_id"],
        unique=True,
        mssql_where=sa.text("is_primary = 1"),
    )

    _seed_roles()
    _backfill_user_roles()

    op.alter_column("roles", "is_active", server_default=None)
    op.alter_column("user_roles", "is_primary", server_default=None)


def _seed_roles() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("name", sa.Unicode(length=50)),
        sa.column("description", sa.Unicode(length=255)),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        roles,
        [
            {"id": uuid.uuid4(), "name": name, "description": description, "is_active": True}
            for name, description in _SEED_ROLES
        ],
    )


def _backfill_user_roles() -> None:
    """Give every existing user a primary `user_roles` row matching their
    current `users.role` value. Legacy role strings outside the seed list get
    their own role row created on the fly rather than being dropped."""
    bind = op.get_bind()

    seeded_names = {name for name, _ in _SEED_ROLES}
    legacy_names = {
        row[0]
        for row in bind.execute(
            sa.text("SELECT DISTINCT role FROM users WHERE role IS NOT NULL")
        ).fetchall()
    }
    unseeded_names = legacy_names - seeded_names

    if unseeded_names:
        roles = sa.table(
            "roles",
            sa.column("id", sa.Uuid(as_uuid=True)),
            sa.column("name", sa.Unicode(length=50)),
            sa.column("description", sa.Unicode(length=255)),
            sa.column("is_active", sa.Boolean()),
        )
        op.bulk_insert(
            roles,
            [
                {
                    "id": uuid.uuid4(),
                    "name": name,
                    "description": "Auto-created from a pre-existing users.role value not in the seed list.",
                    "is_active": True,
                }
                for name in sorted(unseeded_names)
            ],
        )

    role_ids: dict[str, uuid.UUID] = {
        row[1]: row[0] for row in bind.execute(sa.text("SELECT id, name FROM roles")).fetchall()
    }
    buyer_id = role_ids["Buyer"]

    users = bind.execute(sa.text("SELECT id, role FROM users")).fetchall()
    if not users:
        return

    user_roles = sa.table(
        "user_roles",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("user_id", sa.Uuid(as_uuid=True)),
        sa.column("role_id", sa.Uuid(as_uuid=True)),
        sa.column("is_primary", sa.Boolean()),
    )
    op.bulk_insert(
        user_roles,
        [
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                # users.role is NOT NULL with a "Buyer" default (0003), so this
                # fallback only guards against unexpected legacy data - it
                # keeps the "every user has >=1 role" invariant unconditional.
                "role_id": role_ids.get(role_name, buyer_id) if role_name else buyer_id,
                "is_primary": True,
            }
            for user_id, role_name in users
        ],
    )


def downgrade() -> None:
    op.drop_index("uq_user_roles_one_primary_per_user", table_name="user_roles")
    op.drop_index("uq_user_roles_user_id_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_index("uq_roles_name", table_name="roles")
    op.drop_table("roles")
