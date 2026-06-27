"""Monitoring API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.monitoring import MonitoringHealthResponse, RequestMetrics
from app.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get(
    "/health",
    response_model=MonitoringHealthResponse,
    summary="Detailed health with database status",
)
def monitoring_health(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> MonitoringHealthResponse:
    """Return application health including database connectivity."""
    return monitoring_service.health(db)


@router.get(
    "/metrics",
    response_model=RequestMetrics,
    summary="Request counters and slow request totals",
)
def monitoring_metrics(
    _: Annotated[User, Depends(require_viewer)],
) -> RequestMetrics:
    """Return aggregated HTTP request metrics."""
    return monitoring_service.metrics()
