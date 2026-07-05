"""users.role (free-text string) -> users.primary_role_id (FK to roles.id)

0029_roles added the normalized roles/user_roles tables but left users.role
as a plain string for a fast "primary role" read, kept in sync by
application code. That's exactly the kind of denormalization that drifts:
nothing at the database level stopped users.role from ever holding a value
that isn't a real row in `roles`. This migration replaces it with a real
foreign key.

Steps (add-nullable -> backfill -> tighten, so this is safe against
existing rows):
  1. Add users.primary_role_id, nullable.
  2. Backfill it from each user's existing primary user_roles row (written
     by 0029's backfill, so it's already 1:1 with users.role).
  3. Make it NOT NULL and add the FK (ondelete NO ACTION: deleting a role
     that is still someone's primary role must fail loudly, not silently
     orphan/cascade into deleting the user).
  4. Drop the old users.role column (and its default constraint).
  5. Drop user_roles.is_primary and its filtered unique index - redundant
     now that "the" primary role lives in exactly one place
     (users.primary_role_id) instead of two.

Revision ID: 0030_users_primary_role_fk
Revises: 0029_roles
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0030_users_primary_role_fk"
down_revision: str | None = "0029_roles"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# SQL Server auto-names DEFAULT constraints (e.g. "DF__users__role__..."),
# so the one on users.role can't be hardcoded here - look it up and drop it
# dynamically, same approach 0022_sub_sellers.py uses for an auto-named FK.
_DROP_USERS_ROLE_DEFAULT_SQL = """
DECLARE @constraint_name NVARCHAR(200);
SELECT @constraint_name = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE dc.parent_object_id = OBJECT_ID('users') AND c.name = 'role';

IF @constraint_name IS NOT NULL
BEGIN
    DECLARE @sql NVARCHAR(500) = 'ALTER TABLE users DROP CONSTRAINT ' + @constraint_name;
    EXEC sp_executesql @sql;
END
"""


def upgrade() -> None:
    op.add_column("users", sa.Column("primary_role_id", sa.Uuid(as_uuid=True), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE u
            SET u.primary_role_id = ur.role_id
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id AND ur.is_primary = 1
            """
        )
    )

    op.alter_column("users", "primary_role_id", nullable=False)
    op.create_foreign_key(
        "fk_users_primary_role_id_roles",
        "users",
        "roles",
        ["primary_role_id"],
        ["id"],
        ondelete="NO ACTION",
    )
    op.create_index("ix_users_primary_role_id", "users", ["primary_role_id"])

    op.execute(_DROP_USERS_ROLE_DEFAULT_SQL)
    op.drop_column("users", "role")

    op.drop_index("uq_user_roles_one_primary_per_user", table_name="user_roles")
    op.drop_column("user_roles", "is_primary")


def downgrade() -> None:
    op.add_column(
        "user_roles",
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        sa.text(
            """
            UPDATE ur
            SET ur.is_primary = 1
            FROM user_roles ur
            JOIN users u ON u.id = ur.user_id AND u.primary_role_id = ur.role_id
            """
        )
    )
    op.alter_column("user_roles", "is_primary", server_default=None)
    op.create_index(
        "uq_user_roles_one_primary_per_user",
        "user_roles",
        ["user_id"],
        unique=True,
        mssql_where=sa.text("is_primary = 1"),
    )

    op.add_column("users", sa.Column("role", sa.String(length=30), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE u
            SET u.role = r.name
            FROM users u
            JOIN roles r ON r.id = u.primary_role_id
            """
        )
    )
    op.alter_column("users", "role", nullable=False, server_default="Buyer")

    op.drop_index("ix_users_primary_role_id", table_name="users")
    op.drop_constraint("fk_users_primary_role_id_roles", "users", type_="foreignkey")
    op.drop_column("users", "primary_role_id")
