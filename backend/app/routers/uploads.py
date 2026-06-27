"""CSV upload API routes.

Accepts CSV uploads, delegates validation and storage to the CSV service, and
keeps route handlers free of business logic.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin, require_analyst
from app.database import get_db
from app.models.user import User
from app.schemas.upload import UploadListResponse, UploadResponse
from app.schemas.version import FileVersionListResponse, VersionCompareResponse
from app.services.csv_service import CSVUploadError, csv_service
from app.services.dataset_version_service import (
    DatasetVersionError,
    dataset_version_service,
)
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get(
    "",
    response_model=UploadListResponse,
    summary="List recent uploads",
)
def list_uploads(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
) -> UploadListResponse:
    """Return recent CSV uploads for the current user."""
    items = csv_service.list_uploads(db, user=current_user, limit=limit)
    return UploadListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV file",
)
async def upload_csv(
    request: Request,
    file: Annotated[UploadFile, File(description="CSV file to upload")],
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[Session, Depends(get_db)],
    client_sha256: Annotated[str | None, Form()] = None,
    duplicate_action: Annotated[str | None, Form()] = None,
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
            client_sha256=client_sha256,
            duplicate_action=duplicate_action,
            ip_address=get_client_ip(request),
        )
    except CSVUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/versions",
    response_model=FileVersionListResponse,
    summary="List file version history",
)
def list_file_versions(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileVersionListResponse:
    """Return version history for an uploaded file."""
    try:
        dataset_version_service.ensure_access(db, file_id=file_id, user=current_user)
        return dataset_version_service.list_versions(db, file_id=file_id)
    except DatasetVersionError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(exc) == "File not found"
            else status.HTTP_403_FORBIDDEN
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get(
    "/{file_id}/versions/compare",
    response_model=VersionCompareResponse,
    summary="Compare two file versions",
)
def compare_file_versions(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    version_a: int,
    version_b: int,
) -> VersionCompareResponse:
    """Compare metadata between two version entries."""
    try:
        dataset_version_service.ensure_access(db, file_id=file_id, user=current_user)
        return dataset_version_service.compare_versions(
            db,
            file_id=file_id,
            version_a=version_a,
            version_b=version_b,
        )
    except DatasetVersionError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(exc) in {"File not found", "Version not found"}
            else status.HTTP_403_FORBIDDEN
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete(
    "/{file_id}",
    summary="Delete an uploaded CSV file",
)
def delete_upload(
    file_id: int,
    request: Request,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Delete an uploaded file (admin only)."""
    try:
        csv_service.delete_upload(
            db,
            file_id=file_id,
            user=current_user,
            ip_address=get_client_ip(request),
        )
    except CSVUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Uploaded file deleted"}


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
