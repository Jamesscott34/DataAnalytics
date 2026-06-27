"""EDA API routes.

Exposes exploratory data analysis endpoints for uploaded CSV files.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.eda import (
    ColumnSummary,
    EDARequest,
    EDAResponse,
    EDASuggestions,
)
from app.services.eda_service import EDAError, eda_service

router = APIRouter(prefix="/eda", tags=["eda"])


@router.post(
    "/{file_id}",
    response_model=EDAResponse,
    summary="Run EDA on an uploaded file",
)
def run_eda(
    file_id: int,
    request: EDARequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> EDAResponse:
    """Run or return cached EDA for a stored CSV file."""
    try:
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
