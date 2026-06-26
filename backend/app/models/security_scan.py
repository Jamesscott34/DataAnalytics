"""Security scan ORM model.

Stores Python-only scanner results for uploaded CSV files. Does not perform
scanning logic; see ``security_scan_service.py``.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.uploaded_file import UploadedFile


class ScanStatus(enum.StrEnum):
    """Allowed security scan status values."""

    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


class SecurityScan(Base):
    """Persisted Python-only security scan result for an uploaded file."""

    __tablename__ = "security_scans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issues: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    recommended_action: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    file: Mapped["UploadedFile"] = relationship(
        "UploadedFile",
        back_populates="security_scans",
    )

    def issue_list(self) -> list[str]:
        """Return issues as a string list for schema conversion."""
        return [str(issue) for issue in self.issues]
