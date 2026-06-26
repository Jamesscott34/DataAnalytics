"""Authentication and authorisation FastAPI dependencies.

Provides injectable dependencies for resolving the current user and enforcing
role-based access on protected routes.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.auth_service import auth_service
from app.database import get_db
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the authenticated user from a Bearer access token.

    Args:
        credentials: Parsed Authorization header.
        db: Database session.

    Returns:
        Authenticated User ORM instance.

    Raises:
        HTTPException: If the token is missing, invalid, or user not found.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    claims = auth_service.decode_access_token(credentials.credentials)
    user = auth_service.get_user_by_id(db, int(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    """Build a dependency that restricts access to the given roles.

    Args:
        roles: Allowed user roles for the endpoint.

    Returns:
        FastAPI dependency callable.
    """

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        """Verify the current user has an allowed role."""
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


require_admin = require_roles(UserRole.ADMIN)
require_analyst = require_roles(UserRole.ADMIN, UserRole.ANALYST)
require_viewer = require_roles(UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER)
