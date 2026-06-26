"""Standard API error response schemas.

All error responses use the shape documented in the project API standards.
"""

from pydantic import BaseModel, Field


class StandardError(BaseModel):
    """Canonical API error body returned to clients."""

    error: str = Field(..., examples=["validation_error"])
    message: str = Field(..., examples=["Invalid request payload"])
    status_code: int = Field(..., examples=[400])


class ValidationErrorDetail(BaseModel):
    """Field-level validation error detail."""

    loc: list[str | int]
    msg: str
    type: str
