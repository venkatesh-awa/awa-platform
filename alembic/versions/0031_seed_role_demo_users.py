"""Seed two demo accounts per role, all with a real (working) password.

Every role seeded in 0029_roles (Buyer, Seller, Admin, Accountant, Inspector,
Manager, Operations, AuctionsHead) gets two sign-in-ready accounts, so QA/demo
environments have a real login for every role without needing to sign up.
Unlike 0021_seed_uat_seller_users' placeholder hash (those rows are reference
data, not login accounts), these use a real Argon2id hash of the shared demo
password - core.passwords.hash_password is a pure function with no DB/app
dependency, so it's safe to call from a migration.

Credentials: <role><n>@gmail.com, password Secret@123 for every seeded user
(e.g. buyer1@gmail.com / Secret@123).

This also seeds the cross-role scenario the roles/user_roles tables exist for
(see models/role.py, services/role_service.py): the first demo user of
Buyer/Seller/Admin/Inspector/Manager additionally holds a second role, so "a
Seller who also buys" / "an Admin who sometimes sells" is real, queryable
data, not just a theoretical capability of the schema.

Revision ID: 0031_seed_role_demo_users
Revises: 0030_users_primary_role_fk
Create Date: 2026-07-05

"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from core.passwords import hash_password

revision: str = "0031_seed_role_demo_users"
down_revision: str | None = "0030_users_primary_role_fk"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_DEMO_PASSWORD = "Secret@123"  # noqa: S105 - seed/demo credential, not a real secret

# (email, primary_role, full_name, secondary_role | None)
_DEMO_USERS: list[tuple[str, str, str, str | None]] = [
    ("buyer1@gmail.com", "Buyer", "Buyer One", "Seller"),
    ("buyer2@gmail.com", "Buyer", "Buyer Two", None),
    ("seller1@gmail.com", "Seller", "Seller One", "Buyer"),
    ("seller2@gmail.com", "Seller", "Seller Two", None),
    ("admin1@gmail.com", "Admin", "Admin One", "Buyer"),
    ("admin2@gmail.com", "Admin", "Admin Two", None),
    ("accountant1@gmail.com", "Accountant", "Accountant One", None),
    ("accountant2@gmail.com", "Accountant", "Accountant Two", None),
    ("inspector1@gmail.com", "Inspector", "Inspector One", "Seller"),
    ("inspector2@gmail.com", "Inspector", "Inspector Two", None),
    ("manager1@gmail.com", "Manager", "Manager One", "Buyer"),
    ("manager2@gmail.com", "Manager", "Manager Two", None),
    ("operations1@gmail.com", "Operations", "Operations One", None),
    ("operations2@gmail.com", "Operations", "Operations Two", None),
    ("auctionshead1@gmail.com", "AuctionsHead", "AuctionsHead One", None),
    ("auctionshead2@gmail.com", "AuctionsHead", "AuctionsHead Two", None),
]


def _split_name(name: str) -> tuple[str, str]:
    parts = name.strip().split(" ", 1)
    return (parts[0], parts[1] if len(parts) > 1 else "")


def upgrade() -> None:
    bind = op.get_bind()

    role_ids: dict[str, uuid.UUID] = {
        row[1]: row[0] for row in bind.execute(sa.text("SELECT id, name FROM roles")).fetchall()
    }

    insert_user_sql = sa.text(
        """
        INSERT INTO users (id, email, password_hash, first_name, last_name, phone,
                            primary_role_id, is_active, is_email_verified)
        SELECT :id, :email, :password_hash, :first_name, :last_name, NULL,
               :primary_role_id, 1, 1
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = :email)
        """
    )
    insert_user_role_sql = sa.text(
        """
        INSERT INTO user_roles (id, user_id, role_id)
        SELECT :id, :user_id, :role_id
        WHERE NOT EXISTS (
            SELECT 1 FROM user_roles WHERE user_id = :user_id AND role_id = :role_id
        )
        """
    )
    password_hash = hash_password(_DEMO_PASSWORD)

    for email, role_name, full_name, secondary_role_name in _DEMO_USERS:
        first_name, last_name = _split_name(full_name)
        user_id = uuid.uuid4()
        primary_role_id = role_ids[role_name]

        bind.execute(
            insert_user_sql,
            {
                "id": user_id,
                "email": email,
                "password_hash": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "primary_role_id": primary_role_id,
            },
        )

        # Re-fetch: the row (and its real id) may already exist from a prior
        # run of this migration, since user_id above is only used on first
        # insert - user_roles must point at whichever id is actually stored.
        existing_id = bind.execute(
            sa.text("SELECT id FROM users WHERE email = :email"), {"email": email}
        ).scalar_one()

        bind.execute(
            insert_user_role_sql,
            {"id": uuid.uuid4(), "user_id": existing_id, "role_id": primary_role_id},
        )
        if secondary_role_name is not None:
            bind.execute(
                insert_user_role_sql,
                {
                    "id": uuid.uuid4(),
                    "user_id": existing_id,
                    "role_id": role_ids[secondary_role_name],
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    delete_sql = sa.text("DELETE FROM users WHERE email = :email")
    for email, _role_name, _full_name, _secondary in _DEMO_USERS:
        bind.execute(delete_sql, {"email": email})
