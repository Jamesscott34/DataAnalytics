"""EDA API routes.

Exposes exploratory data analysis endpoints for uploaded CSV files.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.eda import (
    ColumnSummary,
    EDAQueuedResponse,
    EDARequest,
    EDAResponse,
    EDASuggestions,
)
from app.schemas.jobs import JobCreateRequest
from app.services.background_service import background_job_service
from app.services.eda_service import EDAError, eda_service

router = APIRouter(prefix="/eda", tags=["eda"])


@router.post(
    "/{file_id}",
    response_model=EDAResponse | EDAQueuedResponse,
    summary="Run EDA on an uploaded file",
    responses={
        202: {
            "description": "EDA queued as a background job for large files",
            "model": EDAQueuedResponse,
        },
    },
)
def run_eda(
    file_id: int,
    request: EDARequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> EDAResponse | JSONResponse:
    """Run or return cached EDA; large files are processed in the background."""
    try:
        if eda_service.should_run_in_background(
            db,
            file_id=file_id,
            force_background=request.force_background,
        ):
            job = background_job_service.enqueue(
                db,
                owner_id=current_user.id,
                request=JobCreateRequest(
                    job_type="eda",
                    payload={
                        "file_id": file_id,
                        "force_refresh": request.force_refresh,
                    },
                ),
                autostart=True,
            )
            payload = EDAQueuedResponse(
                job_id=job.id,
                file_id=file_id,
                message=(
                    "Large file detected. EDA is running in the background; "
                    f"poll /jobs/{job.id} for progress."
                ),
            )
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=payload.model_dump(mode="json"),
            )
        return eda_service.run_for_file(
            db,
            file_id=file_id,
            force_refresh=request.force_refresh,
        )
    except EDAError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}",
    response_model=EDAResponse,
    summary="Get cached EDA results",
    responses={204: {"description": "EDA has not been run for this file yet"}},
)
def get_eda(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> EDAResponse | Response:
    """Return cached EDA output for a file."""
    try:
        return eda_service.get_cached_for_file(db, file_id=file_id)
    except EDAError as exc:
        if "not been run" in str(exc).lower():
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/columns/{column_name}",
    response_model=ColumnSummary,
    summary="Get EDA summary for one column",
)
def get_column_eda(
    file_id: int,
    column_name: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> ColumnSummary:
    """Return EDA details for a single column."""
    try:
        return eda_service.get_column_summary(
            db,
            file_id=file_id,
            column_name=column_name,
        )
    except EDAError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/suggestions",
    response_model=EDASuggestions,
    summary="Get modelling suggestions from EDA",
)
def get_eda_suggestions(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> EDASuggestions:
    """Return suggested targets, features, and analyses."""
    try:
        return eda_service.get_suggestions(db, file_id=file_id)
    except EDAError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
