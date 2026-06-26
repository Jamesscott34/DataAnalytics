"""Temp assets API routes.

Lists CSV files from temp_assets and imports a selected file through the upload
pipeline without requiring a browser file upload.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.upload import AssetListResponse, UploadResponse
from app.services.assets_service import assets_service
from app.services.csv_service import CSVUploadError

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetSelectRequest(BaseModel):
    """Request body for selecting a temp asset."""

    filename: str = Field(min_length=1, max_length=512)
    duplicate_action: str | None = None


@router.get("", response_model=AssetListResponse, summary="List temp asset CSVs")
def list_assets(
    _: Annotated[User, Depends(require_viewer)],
) -> AssetListResponse:
    """List CSV files available in the temp_assets directory."""
    return assets_service.list_assets()


@router.post(
    "/select",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Select a temp asset CSV",
)
def select_asset(
    payload: AssetSelectRequest,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[Session, Depends(get_db)],
) -> UploadResponse:
    """Import a temp asset through validation, scan, and duplicate checks."""
    try:
        return assets_service.select_asset(
            db,
            filename=payload.filename,
            owner_id=current_user.id,
            duplicate_action=payload.duplicate_action,
        )
    except CSVUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
