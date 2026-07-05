"""A seller's sub-seller: a lightweight named contact (name + phone) acting
under a seller/client, not a full authenticateable account. Kept as its own
table rather than another `users` row - production data (the source admin
module's sub-seller list) has no email/login for these, only an id, a name,
a phone number, and the parent seller's user id.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Unicode, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.user import User


class SubSeller(Base):
    __tablename__ = "sub_sellers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # The source admin module's own sub_seller_id (e.g. "1057") - kept for
    # traceability/re-import, not used as our primary key since it's a plain
    # integer from a different system, not a UUID.
    external_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    seller: Mapped[User] = relationship()
