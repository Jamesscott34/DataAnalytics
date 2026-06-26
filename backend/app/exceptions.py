"""Global API exception handlers.

Maps framework and application exceptions to the standard error response shape.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.upload import DuplicateUploadResponse
from app.services.csv_service import DuplicateUploadError
from app.utils.response_utils import build_error_response, build_validation_error


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI application.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(DuplicateUploadError)
    async def duplicate_upload_handler(
        request: Request,
        exc: DuplicateUploadError,
    ) -> JSONResponse:
        """Return structured duplicate upload details for client resolution."""
        body = DuplicateUploadResponse(
            message=(
                "This file matches an existing upload. "
                "Use the existing file or replace it."
            ),
            file_hash=exc.file_hash,
            existing_file=exc.existing_file,
            scan_result=exc.scan_result,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=body.model_dump(mode="json"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Convert HTTP exceptions to standard error JSON."""
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        body = build_error_response(
            error="http_error",
            message=str(exc.detail),
            status_code=exc.status_code,
        )
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Convert request validation errors to standard error JSON."""
        message = "; ".join(
            f"{'.'.join(str(part) for part in err.get('loc', []))}: {err.get('msg')}"
            for err in exc.errors()
        )
        body = build_validation_error(message or "Validation failed")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=body,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Return generic 500 for unexpected errors without leaking internals."""
        body = build_error_response(
            error="internal_error",
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body,
        )
