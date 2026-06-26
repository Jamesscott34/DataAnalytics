"""Audit log API routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogListResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditLogListResponse, summary="List audit logs")
def list_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    event_type: Annotated[str | None, Query()] = None,
    user_id: Annotated[int | None, Query()] = None,
    from_time: Annotated[datetime | None, Query(alias="from")] = None,
    to_time: Annotated[datetime | None, Query(alias="to")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditLogListResponse:
    """List persisted audit events (admin only)."""
    return audit_service.list_logs(
        db,
        event_type=event_type,
        user_id=user_id,
        from_time=from_time,
        to_time=to_time,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{file_id}",
    response_model=AuditLogListResponse,
    summary="List audit logs for a file",
)
def list_audit_logs_for_file(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditLogListResponse:
    """Return audit events for a file (admin or file owner)."""
    try:
        return audit_service.list_for_file(
            db,
            file_id=file_id,
            user=current_user,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
