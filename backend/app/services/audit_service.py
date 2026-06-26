"""Audit logging service.

Persists audit events to the database and emits structured audit log lines.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.uploaded_file import UploadedFile
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogEntry, AuditLogListResponse
from app.utils.logging_utils import log_audit_event


class AuditService:
    """Record and query persisted audit events."""

    def record(
        self,
        db: Session,
        *,
        event_type: str,
        action: str,
        result: str,
        user_id: int | None = None,
        file_id: int | None = None,
        file_hash: str | None = None,
        filename: str | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> AuditLog:
        """Persist an audit event and emit a structured audit log line."""
        log_audit_event(
            event_type=event_type,
            action=action,
            result=result,
            user_id=user_id,
            file_hash=file_hash,
            filename=filename,
            ip_address=ip_address,
            extra=metadata,
        )
        entry = AuditLog(
            user_id=user_id,
            file_id=file_id,
            event_type=event_type,
            action=action,
            result=result,
            file_hash=file_hash,
            filename=filename,
            ip_address=ip_address,
            event_metadata=metadata,
        )
        db.add(entry)
        if commit:
            db.commit()
            db.refresh(entry)
        return entry

    def list_logs(
        self,
        db: Session,
        *,
        event_type: str | None = None,
        user_id: int | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditLogListResponse:
        """Return paginated audit logs for admin review."""
        query = db.query(AuditLog)
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if from_time is not None:
            query = query.filter(AuditLog.created_at >= from_time)
        if to_time is not None:
            query = query.filter(AuditLog.created_at <= to_time)

        total = query.count()
        items = (
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return AuditLogListResponse(
            items=[AuditLogEntry.model_validate(item) for item in items],
            total=total,
        )

    def list_for_file(
        self,
        db: Session,
        *,
        file_id: int,
        user: User,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditLogListResponse:
        """Return audit logs for a file if the caller is admin or owner."""
        file = db.get(UploadedFile, file_id)
        if file is None:
            raise ValueError("File not found")
        if user.role != UserRole.ADMIN and file.owner_id != user.id:
            raise PermissionError("Insufficient permissions")

        query = db.query(AuditLog).filter(
            (AuditLog.file_id == file_id) | (AuditLog.file_hash == file.file_hash)
        )
        total = query.count()
        items = (
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return AuditLogListResponse(
            items=[AuditLogEntry.model_validate(item) for item in items],
            total=total,
        )

    def count_for_event(
        self,
        db: Session,
        *,
        event_type: str,
        action: str,
    ) -> int:
        """Return count of audit entries for a given event type and action."""
        return (
            db.query(func.count(AuditLog.id))
            .filter(
                AuditLog.event_type == event_type,
                AuditLog.action == action,
            )
            .scalar()
            or 0
        )


audit_service = AuditService()
