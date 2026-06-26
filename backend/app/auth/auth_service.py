"""Authentication business logic.

Registers users, validates credentials, issues tokens, and manages refresh
session persistence. Does not parse HTTP requests or return responses.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_utils import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.password_utils import hash_password, verify_password
from app.config import get_settings
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import TokenResponse, UserCreate
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class AuthService:
    """Coordinates user authentication and token lifecycle operations."""

    def register_user(self, db: Session, payload: UserCreate) -> User:
        """Create a new user account with a hashed password.

        Args:
            db: Active database session.
            payload: Registration fields from the client.

        Returns:
            Newly created User ORM instance.

        Raises:
            HTTPException: If registration is disabled or email exists.
        """
        settings = get_settings()
        if not settings.allow_public_registration:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration is disabled",
            )

        return self._create_user(db, payload)

    def admin_create_user(self, db: Session, payload: UserCreate) -> User:
        """Create a user account as an administrator.

        Args:
            db: Active database session.
            payload: User creation fields including optional role.

        Returns:
            Newly created User ORM instance.
        """
        return self._create_user(db, payload)

    def authenticate(self, db: Session, email: str, password: str) -> User:
        """Validate credentials and return the matching active user.

        Args:
            db: Active database session.
            email: Login email address.
            password: Plaintext password.

        Returns:
            Authenticated User instance.

        Raises:
            HTTPException: If credentials are invalid or account inactive.
        """
        user = db.query(User).filter(User.email == email.lower()).first()
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        return user

    def issue_tokens(
        self,
        db: Session,
        user: User,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Issue access and refresh tokens and persist the refresh session.

        Args:
            db: Active database session.
            user: Authenticated user.
            ip_address: Optional client IP for session auditing.
            user_agent: Optional client user-agent string.

        Returns:
            TokenResponse for the client.
        """
        access_token, expires_in = create_access_token(user.id, user.role.value)
        refresh_token, jti, expires_at = create_refresh_token(user.id)
        session = UserSession(
            user_id=user.id,
            refresh_token_jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(session)
        db.commit()
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",  # nosec B106 - OAuth token type label, not a password
            expires_in=expires_in,
        )

    def refresh_tokens(self, db: Session, refresh_token: str) -> TokenResponse:
        """Rotate refresh token and return a new token pair.

        Args:
            db: Active database session.
            refresh_token: Valid refresh JWT from the client.

        Returns:
            New TokenResponse.

        Raises:
            HTTPException: If refresh token is invalid or revoked.
        """
        claims = self._decode_refresh_claims(refresh_token)
        session = (
            db.query(UserSession)
            .filter(UserSession.refresh_token_jti == claims["jti"])
            .first()
        )
        if session is None or session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or unknown",
            )

        user = db.query(User).filter(User.id == int(claims["sub"])).first()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        session.revoked_at = datetime.now(UTC)
        db.commit()
        return self.issue_tokens(db, user)

    def logout(self, db: Session, refresh_token: str | None) -> None:
        """Revoke a refresh token session if provided.

        Args:
            db: Active database session.
            refresh_token: Refresh JWT to revoke, if supplied.
        """
        if not refresh_token:
            return
        try:
            claims = self._decode_refresh_claims(refresh_token)
        except HTTPException:
            return
        session = (
            db.query(UserSession)
            .filter(UserSession.refresh_token_jti == claims["jti"])
            .first()
        )
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            db.commit()

    def get_user_by_id(self, db: Session, user_id: int) -> User | None:
        """Load a user by primary key.

        Args:
            db: Active database session.
            user_id: User identifier.

        Returns:
            User instance or None if not found.
        """
        return db.query(User).filter(User.id == user_id).first()

    def _create_user(self, db: Session, payload: UserCreate) -> User:
        """Persist a new user after duplicate-email validation."""
        email = payload.email.lower()
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(
            "user_registered",
            extra={"user_id": user.id, "role": user.role.value},
        )
        return user

    def _decode_refresh_claims(self, refresh_token: str) -> dict[str, str]:
        """Decode refresh token and validate token type."""
        from jose import JWTError

        try:
            claims = decode_token(refresh_token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc

        if claims.get("type") != TOKEN_TYPE_REFRESH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token type",
            )
        return claims

    def decode_access_token(self, token: str) -> dict[str, str]:
        """Decode access token and validate token type.

        Args:
            token: Bearer access JWT.

        Returns:
            Token claims including ``sub`` and ``role``.

        Raises:
            HTTPException: If token is invalid, expired, or wrong type.
        """
        from jose import JWTError

        try:
            claims = decode_token(token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            ) from exc

        if claims.get("type") != TOKEN_TYPE_ACCESS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token type",
            )
        return claims


auth_service = AuthService()
