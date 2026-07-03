"""Password hashing using Argon2id (OWASP's recommended algorithm).

Kept separate from token handling (core/access_tokens.py) and from the external
IdP verifier (core/security.py) so each concern has a single home. The hasher's
parameters live with the library defaults, which are tuned to be interactive-safe
and are encoded into every hash - so raising them later automatically triggers a
transparent rehash on the next successful login (see needs_rehash).
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Return an Argon2id hash (algorithm + parameters + salt are embedded)."""
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time verify. Returns False on mismatch or a malformed stored hash
    rather than raising, so callers get a simple boolean."""
    try:
        return _hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when the stored hash was made with weaker parameters than the current
    policy - the caller should re-hash the (already verified) password and persist it."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False
