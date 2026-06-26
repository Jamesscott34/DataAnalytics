"""Asset integrity manifest API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_analyst
from app.models.user import User
from app.schemas.asset_integrity import (
    ApplyIntegrityChangesRequest,
    InitializeManifestRequest,
    IntegrityActionResponse,
    IntegrityStatusResponse,
    UnlockManifestRequest,
)
from app.services.asset_integrity_service import (
    AssetIntegrityError,
    asset_integrity_service,
)

router = APIRouter(prefix="/asset-integrity", tags=["asset-integrity"])


@router.get(
    "/status",
    response_model=IntegrityStatusResponse,
    summary="Get asset integrity status",
)
def get_integrity_status(
    _: Annotated[User, Depends(require_analyst)],
) -> IntegrityStatusResponse:
    """Return manifest state and pending folder changes."""
    return asset_integrity_service.get_status()


@router.post(
    "/initialize",
    response_model=IntegrityActionResponse,
    summary="Create password-protected integrity manifest",
)
def initialize_manifest(
    payload: InitializeManifestRequest,
    _: Annotated[User, Depends(require_analyst)],
) -> IntegrityActionResponse:
    """Create the encrypted manifest and record current folder hashes."""
    try:
        return asset_integrity_service.initialize_manifest(
            payload.password,
            payload.confirm_password,
        )
    except AssetIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/unlock",
    response_model=IntegrityActionResponse,
    summary="Unlock integrity manifest",
)
def unlock_manifest(
    payload: UnlockManifestRequest,
    _: Annotated[User, Depends(require_analyst)],
) -> IntegrityActionResponse:
    """Unlock the encrypted manifest for this server session."""
    try:
        return asset_integrity_service.unlock_manifest(payload.password)
    except AssetIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/apply",
    response_model=IntegrityActionResponse,
    summary="Apply approved integrity manifest changes",
)
def apply_integrity_changes(
    payload: ApplyIntegrityChangesRequest,
    _: Annotated[User, Depends(require_analyst)],
) -> IntegrityActionResponse:
    """Add, update, or remove manifest entries after user review."""
    try:
        return asset_integrity_service.apply_changes(
            add_or_update=payload.add_or_update,
            remove=payload.remove,
        )
    except AssetIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
