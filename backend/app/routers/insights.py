"""Generated insight API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.insights import InsightRequest, InsightResponse
from app.services.insight_service import InsightError, insight_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post(
    "/generate",
    response_model=InsightResponse,
    summary="Generate a plain-English analysis insight",
)
def generate_insight(
    payload: InsightRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> InsightResponse:
    """Generate and store an insight for a result id."""
    try:
        return insight_service.generate(db, payload)
    except InsightError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/by-job/{job_id}",
    response_model=InsightResponse,
    summary="Get latest generated insight for a job",
)
def get_insight_by_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> InsightResponse:
    """Return the latest stored insight for a job id."""
    try:
        return insight_service.get_by_job(db, job_id)
    except InsightError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{insight_id}",
    response_model=InsightResponse,
    summary="Get a generated insight",
)
def get_insight(
    insight_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> InsightResponse:
    """Return a stored insight by id."""
    try:
        return insight_service.get(db, insight_id)
    except InsightError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
