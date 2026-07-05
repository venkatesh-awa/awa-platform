"""seed real seller/client accounts from the live Al Wataneya UAT admin
module's user list, so the "Add a New Car" form's Client Name / Sub Seller
dropdowns have real data to search instead of an empty local dev DB.

The source system tracks multi-role membership via a semicolon-separated
`job_title` string (e.g. "seller;buyer;admin"); this app's `users.role` is a
single flat value. Every row here has "seller" in its source job_title (all
are `is_seller: "1"`), which is exactly the population the Client/Sub Seller
search needs (it filters on `role == "Seller"`), so role is set to "Seller"
uniformly - preserving the source's full multi-role model would require a
broader schema change to models/user.py, out of scope here.

password_hash is a placeholder, not a real bcrypt hash: these are reference
records for the seller-lookup feature, not local sign-in accounts, and an
invalid hash means a login attempt against one of these emails simply fails
password verification rather than silently succeeding.

Revision ID: 0021_seed_uat_seller_users
Revises: 0020_vehicle_submissions
Create Date: 2026-07-05

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021_seed_uat_seller_users"
down_revision: str | None = "0020_vehicle_submissions"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_PLACEHOLDER_PASSWORD_HASH = "external-uat-import-no-login"  # noqa: S105 - not a real credential

# (user_id, name, email, phone) - verbatim from the UAT admin module's user
# list; every row is is_seller="1" / is_active="Active" in the source.
_SELLER_USERS: list[tuple[str, str, str, str]] = [
    ("5a8163ab-9ce4-4041-ae54-876d110ec035", "testuat", "testuat1@gmail.com", "+9716362626262"),
    ("621e04d1-834b-4d68-a5ef-d47d81bbad6f", "Israa Seller", "kondalasivakumar19@gmail.com", "+971801902703"),
    ("10d9c04e-5b81-4fd1-8415-ff32f9fd5e25", "buyertestuser", "testuseruat@gmail.com", "+971767766767"),
    ("ee36d0ff-120b-4c72-b227-4413b0a710fe", "Seller One", "sellerone@gmail.com", "+971808808808"),
    ("f7814baf-7d5d-4f88-a020-06c34164ba15", "selleri", "selleri@gmail.com", "+971708708709"),
    ("ba0f914a-e84e-4c23-bea2-f80eeab1e876", "Buyer Test User", "buyertestuser@gmail.com", "+971808089090"),
    ("496bcba0-516c-41d5-b89e-4dd65d72afce", "selltest", "selltest@gmail.com", "+971783737334"),
    ("d43d43a2-1da6-4445-b025-03225f54b4ef", "Seller Test User", "sellertestuser@gmail.com", "+971909909090"),
    ("77362c91-303b-493d-ad56-fe9585a57287", "Test Seller", "testseller@gmail.com", "+971990099000"),
    ("e426ba72-1299-40be-a63f-0e35db1ce85f", "tcont", "tcont@gmail.com", "+9717473838383"),
    ("c19e4c20-bf06-47e0-a208-9716abef66dc", "Sriteja Seller", "sritejaseller@gmail.com", "+971908123096"),
    ("6921bd9d-d877-4e62-b6d6-1da03ad50576", "fone", "fone@gmail.com", "+971726262726"),
    ("148de327-2a1d-451e-b6a0-f76c24fda26c", "Anuritha Seller One", "anuritha@agilitics.edu.sg", "+971701348846"),
    ("80ef87cd-643d-4c64-8e7f-3d62803aa37c", "Shishir Patel Seller", "rahanpatel364@gmail.com", "+971908876098"),
    ("bb5a636b-4b82-4514-93b5-d7cfdd6e1f1c", "Shishir Patel Buyer", "shishirpatelbuyer@gmail.com", "+971809107308"),
    ("aa4c90c2-0c60-4628-a698-0b7ad8d3874e", "Krishna Seller", "saikohliyadav@gmail.com", "+971876098709"),
    ("cb7ba034-65ba-4c3d-b268-5832c719fef4", "Dinesh Seller One", "dineshsellerone@gmail.com", "+971809807806"),
    ("3fef3e24-09d7-4abb-b944-c02bc19f0b18", "Shishir Seller", "shishirpatel123@gmail.com", "+971902109876"),
    ("90a3836e-759f-4a1a-9de1-95b856dca05b", "signtest", "signtest@gmail.com", "+9717373737337"),
    ("942e5067-2c6d-44a9-b2e0-410893ca7694", "txselll", "txselll@gmail.com", "+971737362626"),
    ("80037bad-74d2-4ccd-85cb-d552236b40f4", "txsell", "txsell@gmail.com", "+971567567576"),
    ("5e75fe49-07b6-4741-b94e-b8b5c7be45f3", "sellse", "sesell@gmail.com", "+971675675667"),
    ("cda2b6f4-4833-4c15-90b9-ccc68544a33c", "Dinesh Seller", "saisravan@agilitics.edu.sg", "+971762098108"),
    ("1ccfaa58-2c95-4fba-9992-8d1eb916b08e", "alwataneyaseller", "alwataneyaseller@gmail.com", "+971709832165"),
    ("02c84c17-86a4-40b2-acff-f93bffc16ac2", "alwatneyabuyer", "alwatneyabuyer@gmail.com", "+971987612098"),
    ("667f7610-4cfc-4554-a8df-9353ba8126b1", "uatcool", "uatcool@gmail.com", "+971637366262"),
    ("be99cb06-8bc4-4e80-aa97-8b3576a53c05", "AWA Buyer Ten", "awabuyerten@gmail.com", "+971832098321"),
    ("ea27ab1f-1733-45a6-8def-114ea670d7ce", "testog", "testog@gmail.com", "+971737733737"),
    ("0ebb016b-2c56-4aad-9a8a-ab459c0e3c7c", "tbuyer", "tbuyer@gmail.com", "+971727262628"),
    ("0a1adc14-43ca-4da6-a79b-e03e4dc7e569", "AWA Buyer Seven", "awabuyerseven@gmail.com", "+971876209187"),
    ("9e309d19-1acf-4e7b-a824-706b0f902e46", "Anuritha Seller", "anuritha.j@gmail.com", "+971876345098"),
    ("f3791bbe-955f-433b-a37e-8313e8881d80", "testcoone", "testcoone@gmail.com", "+971727262627"),
    ("64841bc9-7016-486a-8fe0-1cbf1dea2cad", "testcont", "testcont@gmail.com", "+971827272729"),
    ("071ba597-167a-4e69-a653-55b9e96c66ae", "anubuyer", "anubuyer@gmail.com", "+971656767889"),
    ("49f8ef95-2a57-4098-bb80-d241c4e4d8d7", "AWA Seller One", "awasellerone@gmail.com", "+971783903186"),
    (
        "bada7a1f-c2a8-4ed4-9aae-ed89fd1d593c",
        "Krishna Inspection Executive",
        "krishnaexecutive@gmail.com",
        "+97156363773",
    ),
    (
        "baa4f6d7-fbd7-4f8c-8f23-56b2ac9035b4",
        "Sravan Washing Assistant",
        "sravanwashing@gmail.com",
        "+97173827272",
    ),
    ("875e7df1-06f8-4bc6-a7e3-98de10ede18e", "Dinesh Yard Assistant", "dineshyard@gmail.com", "+97173622772"),
    ("38744230-af85-4420-aae6-bcb6b8f81231", "teja yard", "tejayard@gmail.com", "+97173837373"),
    ("015de271-b7d4-4977-ba27-38faef9d7e0e", "Krishna Reddy S V", "udayasheelam8108@gmail.com", "+971632986532"),
    ("abd08c17-144b-47d0-b6f1-c933d75d7e9f", "AWA Admin", "awa.admin@gmail.com", "+971638190288"),
    ("ec291db2-71a0-4368-a18a-875f72c66220", "AWA Admin1", "awa.admin@gmail1.com", "+97191111111"),
    ("b518e8f8-d972-43b5-8df5-34c2697bde6f", "sravanbuy", "sravanbuy@gmail.com", "+971567976568"),
    ("9f62f75f-c3fb-4788-b7cb-8dc96c1b692e", "kishorebuyer", "kishorebuyer@gmail.com", "+971678534678"),
    ("ba45e9a0-efb9-4e62-8f73-5f4e37f91a86", "kishore", "kishore@gmail.com", "+971456789754"),
    ("9c0ba8bf-6da1-4ff1-896d-1fe16853d16a", "Shishir Sai", "shishirsai@gmail.com", "+971394573998"),
    ("870c326c-9434-487a-9d98-3782a6cb5c1d", "sdfsdf", "dsgsfs@gmail.com", "+971123456789"),
    ("3bab5430-d938-4808-b544-990d98e77db0", "saisravanam", "sravan@gmail.com", "+971987987654"),
    ("db843fb7-b7c4-4f8b-a01e-e244c49b46ab", "Sai K", "sai.k@gmail.com", "+971884747474"),
    ("744cce04-3d9f-4fa7-8044-fcd428ec4565", "Sheshu", "sheshu@gmail.com", "+971979879788"),
]


def _split_name(name: str) -> tuple[str, str]:
    parts = name.strip().split(" ", 1)
    return (parts[0], parts[1] if len(parts) > 1 else "")


def upgrade() -> None:
    bind = op.get_bind()
    insert_sql = sa.text(
        """
        INSERT INTO users (id, email, password_hash, first_name, last_name, phone, role,
                            is_active, is_email_verified)
        SELECT :id, :email, :password_hash, :first_name, :last_name, :phone, 'Seller', 1, 0
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = :email)
        """
    )
    for user_id, name, email, phone in _SELLER_USERS:
        first_name, last_name = _split_name(name)
        bind.execute(
            insert_sql,
            {
                "id": user_id,
                "email": email.lower(),
                "password_hash": _PLACEHOLDER_PASSWORD_HASH,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    delete_sql = sa.text("DELETE FROM users WHERE id = :id AND password_hash = :placeholder")
    for user_id, _name, _email, _phone in _SELLER_USERS:
        bind.execute(delete_sql, {"id": user_id, "placeholder": _PLACEHOLDER_PASSWORD_HASH})
