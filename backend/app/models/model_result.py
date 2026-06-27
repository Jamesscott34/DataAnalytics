"""Persisted ML and analytics result ORM model."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class ModelResult(Base):
    """SQL persistence for analysis outputs (EDA, ML, business KPIs)."""

    __tablename__ = "model_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    result_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    job_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("analysis_jobs.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    file_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    result_type: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    explainability: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
