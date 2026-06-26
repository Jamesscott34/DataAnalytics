"""Standard API response builders.

Constructs consistent success and error payloads for routers and exception
handlers. Does not perform HTTP encoding; routers return these dicts/models.
"""

from typing import Any

from fastapi import status

from app.schemas.errors import StandardError


def build_error_response(
    error: str,
    message: str,
    status_code: int,
) -> dict[str, Any]:
    """Build a standard error response dictionary.

    Args:
        error: Machine-readable error type identifier.
        message: Human-readable error detail safe for clients.
        status_code: HTTP status code for the error.

    Returns:
        Dictionary matching the StandardError schema.
    """
    return StandardError(
        error=error,
        message=message,
        status_code=status_code,
    ).model_dump()


def build_not_found(message: str = "Resource not found") -> dict[str, Any]:
    """Build a 404 not-found error response.

    Args:
        message: Detail message for the missing resource.

    Returns:
        Standard error payload with status 404.
    """
    return build_error_response("not_found", message, status.HTTP_404_NOT_FOUND)


def build_validation_error(message: str) -> dict[str, Any]:
    """Build a 422 validation error response.

    Args:
        message: Summary of validation failure.

    Returns:
        Standard error payload with status 422.
    """
    return build_error_response(
        "validation_error",
        message,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
