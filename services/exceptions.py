"""Domain exceptions raised by the services layer.

Deliberately framework-agnostic (no FastAPI/HTTPException here) so the same
service functions are reusable from the REST API, the auction worker, and
future callers (CLI tools, other workers) without dragging in a web
framework dependency. Each caller translates these into whatever error
surface makes sense for it - see api/v1/auctions.py for the HTTP mapping.
"""

from __future__ import annotations


class AuctionNotFoundError(Exception):
    def __init__(self, auction_id: object) -> None:
        self.auction_id = auction_id
        super().__init__(f"Auction not found: {auction_id}")


class AuctionNotLiveError(Exception):
    def __init__(self, auction_id: object, status: str) -> None:
        self.auction_id = auction_id
        self.status = status
        super().__init__(f"Auction {auction_id} is not accepting bids (status={status})")


class BidNotEligibleError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class BidPublishError(Exception):
    """Raised when the bid could not be durably published to the event backbone."""


class MalformedBidEvent(Exception):
    """Raised when a message consumed off the Kafka bids topic doesn't parse as
    a valid bid envelope - treated as a poison message by the auction worker,
    not retried indefinitely."""


# --- Authentication (local email/password) ---


class EmailAlreadyRegisteredError(Exception):
    """Sign-up attempted with an email that already has an account."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsError(Exception):
    """Sign-in failed - wrong email or password. Deliberately does not say which,
    to avoid confirming which emails have accounts."""


class AccountInactiveError(Exception):
    """The account exists but has been deactivated."""


class AccountLockedError(Exception):
    """Too many failed sign-ins; the account is temporarily locked."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Account locked; retry in {retry_after_seconds}s")


class InvalidTokenError(Exception):
    """A refresh / password-reset / email-verification token is unknown, already
    used, revoked, or expired. Uniform for all cases so callers don't leak which."""


# --- Vehicle intake ("Add a New Car" form) ---


class VehicleLookupNotFoundError(Exception):
    """A referenced lookup id (make/model/branch/color/etc.) or client/sub-seller
    user id doesn't exist or isn't active."""

    def __init__(self, field: str, value: object) -> None:
        self.field = field
        self.value = value
        super().__init__(f"Invalid {field}: {value}")


class DuplicateChassisNumberError(Exception):
    """A vehicle submission with this chassis number already exists."""

    def __init__(self, chassis_number: str) -> None:
        self.chassis_number = chassis_number
        super().__init__(f"Chassis number already submitted: {chassis_number}")


# --- Roles ---


class RoleNotFoundError(Exception):
    """A role name doesn't exist in the `roles` table."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Role not found: {name}")


class LastRoleRemovalError(Exception):
    """Refused to revoke a user's only remaining role - every user must keep
    at least one role."""

    def __init__(self, user_id: object) -> None:
        self.user_id = user_id
        super().__init__(f"Cannot remove the last role of user {user_id}")
