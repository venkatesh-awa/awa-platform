"""RBAC constants shared across routers: which roles count as "staff" (i.e.
not a pure marketplace Buyer/Seller), and which staff sections additionally
require a specific role on top of Admin. See models/role.py for the full seed
list and api/deps.require_local_role for the dependency this backs.
"""

from __future__ import annotations

STAFF_ROLES = ("Admin", "Manager", "Operations", "Accountant", "Inspector", "AuctionsHead")

# Admin section key (the path segment right after "/admin/") -> extra roles
# required on top of STAFF_ROLES membership. Sections not listed here are
# open to any staff role.
SECTION_ROLE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "management": ("Admin", "Manager"),
    "accountant": ("Admin", "Accountant"),
}
