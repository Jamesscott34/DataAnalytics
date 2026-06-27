"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Credentials for user login."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    """Refresh token exchange payload."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Optional refresh token to revoke on logout."""

    refresh_token: str | None = None


class UserCreate(BaseModel):
    """Fields required to register or create a user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = UserRole.VIEWER


class UserRead(BaseModel):
    """Public user profile returned by the API."""

    id: int
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Admin fields for updating a user account."""

    role: UserRole | None = None
    is_active: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)


class TokenResponse(BaseModel):
    """JWT access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(TokenResponse):
    """Login payload including tokens and the authenticated user profile."""

    user: UserRead
