"""CSV upload API routes.

Accepts CSV uploads, delegates validation and storage to the CSV service, and
keeps route handlers free of business logic.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin, require_analyst
from app.database import get_db
from app.models.user import User
from app.schemas.upload import UploadResponse
from app.services.csv_service import CSVUploadError, csv_service

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV file",
)
async def upload_csv(
    file: Annotated[UploadFile, File(description="CSV file to upload")],
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[Session, Depends(get_db)],
) -> UploadResponse:
    """Upload a CSV file after validation and deduplication."""
    content = await file.read()
    try:
        return csv_service.upload_csv(
            db,
            filename=file.filename or "",
            content=content,
            owner_id=current_user.id,
            mime_type=file.content_type,
        )
    except CSVUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/guard", summary="Analyst upload permission check")
def upload_permission_check(
    _: Annotated[User, Depends(require_analyst)],
) -> dict[str, bool]:
    """Verify the caller may upload files (analyst or admin)."""
    return {"allowed": True}


@router.delete("/guard", summary="Admin delete permission check")
def delete_permission_check(
    _: Annotated[User, Depends(require_admin)],
) -> dict[str, bool]:
    """Verify the caller may delete files (admin only)."""
    return {"allowed": True}
