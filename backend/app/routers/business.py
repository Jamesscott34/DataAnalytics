"""Business analytics API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.business import BusinessAnalyticsRequest, BusinessReport
from app.services.business_analytics_service import (
    BusinessAnalyticsError,
    business_analytics_service,
)

router = APIRouter(prefix="/business", tags=["business"])


@router.post(
    "/{file_id}/analyze",
    response_model=BusinessReport,
    summary="Analyze business KPIs for an uploaded CSV",
)
def analyze_business(
    file_id: int,
    request: BusinessAnalyticsRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> BusinessReport:
    """Compute revenue, cost, margin, and monthly trend KPIs."""
    try:
        return business_analytics_service.analyze(db, file_id=file_id, request=request)
    except BusinessAnalyticsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/kpis",
    response_model=BusinessReport,
    summary="Get latest business KPI report for a file",
)
def get_business_kpis(
    file_id: int,
    _: Annotated[User, Depends(require_viewer)],
) -> BusinessReport:
    """Return the latest KPI report for a file."""
    try:
        return business_analytics_service.get_latest_for_file(file_id)
    except BusinessAnalyticsError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
