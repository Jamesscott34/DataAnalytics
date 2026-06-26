"""JWT creation and validation utilities.

Issues short-lived access tokens and longer-lived refresh tokens. Refresh
token JTIs are persisted in ``user_sessions`` for revocation support.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt

from app.config import get_settings

# These constants are JWT claim labels, not secrets or credentials.
TOKEN_TYPE_ACCESS = "access"  # nosec B105
TOKEN_TYPE_REFRESH = "refresh"  # nosec B105


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    """Create a signed JWT access token.

    Args:
        user_id: Database primary key for the authenticated user.
        role: User role string stored in the token claims.

    Returns:
        Tuple of encoded token and expiry duration in seconds.
    """
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = _utc_now() + expires_delta
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": TOKEN_TYPE_ACCESS,
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, int(expires_delta.total_seconds())


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """Create a signed JWT refresh token with a unique JTI.

    Args:
        user_id: Database primary key for the authenticated user.

    Returns:
        Tuple of token string, JTI, and expiry timestamp.
    """
    settings = get_settings()
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    expire = _utc_now() + expires_delta
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(user_id),
        "type": TOKEN_TYPE_REFRESH,
        "jti": jti,
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, jti, expire


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT.

    Args:
        token: Encoded JWT string from the Authorization header or body.

    Returns:
        Decoded token claims.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    settings = get_settings()
    return dict(
        jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    )
