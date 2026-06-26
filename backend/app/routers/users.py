"""User management API routes (admin).

Lists and manages user accounts. All endpoints require the Admin role.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.auth_service import auth_service
from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(db: Session, user_id: int) -> User:
    """Load a user or raise HTTP 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create user (admin)",
)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> User:
    """Create a user with a role assigned by an administrator."""
    return auth_service.admin_create_user(db, payload)


@router.get("", response_model=list[UserRead], summary="List all users")
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> list[User]:
    """Return all registered users."""
    return db.query(User).order_by(User.id).all()


@router.get("/{user_id}", response_model=UserRead, summary="Get user by ID")
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> User:
    """Return a single user by identifier."""
    return _get_user_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserRead, summary="Update user")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> User:
    """Update role, active status, or display name for a user."""
    user = _get_user_or_404(db, user_id)
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.full_name is not None:
        user.full_name = payload.full_name

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", summary="Delete user")
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> dict[str, str]:
    """Permanently delete a user account."""
    user = _get_user_or_404(db, user_id)
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
