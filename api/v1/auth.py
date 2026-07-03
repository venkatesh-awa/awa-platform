"""Local authentication REST endpoints - a thin controller over
services/auth_service.py. Handles only HTTP concerns: routing, request/response
schemas, translating domain exceptions to status codes, and extracting the
bearer token for the authenticated `/me` endpoint.

Token issuance here is for the platform's own email/password accounts and is
independent of the external-IdP verification in core/security.py (which remains
the path for Azure B2C / UAE Pass tokens).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db_session
from core.access_tokens import decode_access_token
from core.logging import get_logger
from models.user import User
from schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SignInRequest,
    SignOutRequest,
    SignUpRequest,
    TokenPair,
    UserRead,
    VerifyEmailRequest,
)
from services import auth_service
from services.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

_bearer_scheme = HTTPBearer(auto_error=False)

# Generic reset copy - identical whether or not the email exists, so the
# endpoint can't be used to enumerate registered accounts.
_RESET_SENT_MESSAGE = "If an account exists for that email, a reset link has been sent."


async def get_current_local_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency: resolve the User from a locally-issued access token."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials:
        raise unauthorized

    claims = decode_access_token(credentials.credentials)
    if claims is None:
        raise unauthorized

    try:
        user_id = uuid.UUID(claims.subject)
    except ValueError as exc:
        raise unauthorized from exc

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def sign_up(
    payload: SignUpRequest, db: AsyncSession = Depends(get_db_session)
) -> User:
    try:
        result = await auth_service.sign_up(db, payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        ) from exc
    # Hand the raw verification token to the email layer. Emailing is out of
    # scope here; log it (redacted in prod sinks) as the integration seam.
    logger.info("email_verification_token_issued", user_id=str(result.user.id))
    return result.user


@router.post("/signin", response_model=TokenPair)
async def sign_in(
    payload: SignInRequest, db: AsyncSession = Depends(get_db_session)
) -> TokenPair:
    try:
        _, tokens = await auth_service.sign_in(db, payload.email, payload.password)
        return tokens
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to failed sign-in attempts",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except AccountInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        ) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        ) from exc


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest, db: AsyncSession = Depends(get_db_session)
) -> TokenPair:
    try:
        return await auth_service.refresh(db, payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        ) from exc


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    payload: SignOutRequest, db: AsyncSession = Depends(get_db_session)
) -> Response:
    # Idempotent by design - revoking an already-invalid token still returns 204.
    await auth_service.sign_out(db, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db_session)
) -> MessageResponse:
    raw_token = await auth_service.request_password_reset(db, payload.email)
    if raw_token is not None:
        # Integration seam for the email layer (send FRONTEND_BASE_URL/reset?token=...).
        logger.info("password_reset_token_issued")
    return MessageResponse(message=_RESET_SENT_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db_session)
) -> MessageResponse:
    try:
        await auth_service.reset_password(db, payload.token, payload.new_password)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
        ) from exc
    return MessageResponse(message="Your password has been reset. You can now sign in.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db_session)
) -> MessageResponse:
    try:
        await auth_service.verify_email(db, payload.token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token"
        ) from exc
    return MessageResponse(message="Your email has been verified.")


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_local_user)) -> User:
    return user
