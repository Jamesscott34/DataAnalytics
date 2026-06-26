"""Authentication API routes.

Handles registration, login, token refresh, logout, and the current-user
profile endpoint. Business logic is delegated to ``AuthService``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth.auth_service import auth_service
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    """Extract client IP and user-agent for session metadata."""
    ip_address = request.client.host if request.client else None
    return ip_address, request.headers.get("user-agent")


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Register a user when public registration is enabled."""
    return auth_service.register_user(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT tokens",
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Validate credentials and return access and refresh tokens."""
    user = auth_service.authenticate(db, payload.email, payload.password)
    ip_address, user_agent = _client_meta(request)
    return auth_service.issue_tokens(
        db,
        user,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new token pair",
)
def refresh(
    payload: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Rotate refresh token and issue new credentials."""
    return auth_service.refresh_tokens(db, payload.refresh_token)


@router.post("/logout", summary="Revoke refresh token session")
def logout(
    payload: LogoutRequest,
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    """Logout by revoking the supplied refresh token."""
    auth_service.logout(db, payload.refresh_token)
    return JSONResponse({"message": "logged out"})


@router.get("/me", response_model=UserRead, summary="Get current user profile")
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Return the authenticated user's profile."""
    return current_user
