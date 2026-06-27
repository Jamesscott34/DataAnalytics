"""Background job API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst
from app.database import get_db
from app.models.user import User
from app.schemas.jobs import JobCreateRequest, JobListResponse, JobResponse
from app.services.background_service import BackgroundJobError, background_job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a background analysis job",
)
def create_job(
    request: JobCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> JobResponse:
    """Queue a background job and start worker execution."""
    return background_job_service.enqueue(
        db,
        owner_id=current_user.id,
        request=request,
        autostart=True,
    )


@router.get("", response_model=JobListResponse, summary="List recent jobs")
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> JobListResponse:
    """Return recent jobs for the current analyst."""
    items = background_job_service.list_jobs(db, owner_id=current_user.id)
    return JobListResponse(items=items, total=len(items))


@router.get("/{job_id}", response_model=JobResponse, summary="Get job progress")
def get_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> JobResponse:
    """Return a job's latest progress."""
    try:
        return background_job_service.get_job(db, job_id=job_id, owner_id=current_user.id)
    except BackgroundJobError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{job_id}/cancel", response_model=JobResponse, summary="Cancel a job")
def cancel_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> JobResponse:
    """Cancel a queued or running job."""
    try:
        return background_job_service.cancel(db, job_id=job_id, owner_id=current_user.id)
    except BackgroundJobError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
