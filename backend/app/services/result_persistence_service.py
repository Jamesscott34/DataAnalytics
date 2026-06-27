"""Persist and restore analysis results in SQL."""

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.models.model_result import ModelResult

T = TypeVar("T", bound=BaseModel)


class ResultPersistenceError(ValueError):
    """Raised when a persisted result cannot be loaded."""


class ResultPersistenceService:
    """Store model outputs in the model_results table."""

    def persist(
        self,
        db: Session,
        *,
        result_id: str,
        file_id: int,
        result_type: str,
        payload: dict[str, Any],
        algorithm: str | None = None,
        metrics: dict[str, Any] | None = None,
        explainability: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> ModelResult:
        """Insert or replace a persisted result row."""
        existing = (
            db.query(ModelResult).filter(ModelResult.result_id == result_id).first()
        )
        if existing is not None:
            existing.file_id = file_id
            existing.job_id = job_id
            existing.result_type = result_type
            existing.algorithm = algorithm
            existing.metrics = metrics or {}
            existing.payload = payload
            existing.explainability = explainability
            record = existing
        else:
            record = ModelResult(
                result_id=result_id,
                file_id=file_id,
                job_id=job_id,
                result_type=result_type,
                algorithm=algorithm,
                metrics=metrics or {},
                payload=payload,
                explainability=explainability,
            )
            db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def save_model(
        self,
        db: Session,
        cache: dict[str, T],
        result: T,
        *,
        result_type: str,
        algorithm: str | None = None,
        job_id: str | None = None,
    ) -> T:
        """Cache in memory and persist a Pydantic result model."""
        result_id = str(getattr(result, "result_id"))
        file_id = int(getattr(result, "file_id"))
        cache[result_id] = result
        metrics: dict[str, Any] = {}
        explainability: dict[str, Any] | None = None
        metric_value = getattr(result, "metrics", None)
        if metric_value is not None:
            metrics = (
                metric_value.model_dump()
                if isinstance(metric_value, BaseModel)
                else dict(metric_value)
            )
        explain_value = getattr(result, "explainability", None)
        if explain_value is not None:
            explainability = (
                explain_value.model_dump()
                if isinstance(explain_value, BaseModel)
                else dict(explain_value)
            )
        self.persist(
            db,
            result_id=result_id,
            file_id=file_id,
            result_type=result_type,
            algorithm=algorithm,
            metrics=metrics,
            payload=result.model_dump(mode="json"),
            explainability=explainability,
            job_id=job_id,
        )
        return result

    def load_model(
        self,
        db: Session | None,
        cache: dict[str, T],
        result_id: str,
        model: type[T],
    ) -> T | None:
        """Return a cached or SQL-backed result model."""
        cached = cache.get(result_id)
        if cached is not None:
            return cached
        if db is None:
            return None
        restored = self.restore(db, result_id=result_id, model=model)
        if restored is not None:
            cache[result_id] = restored
        return restored

    def load_payload(self, db: Session, *, result_id: str) -> dict[str, Any] | None:
        """Return stored payload dict or None."""
        record = (
            db.query(ModelResult).filter(ModelResult.result_id == result_id).first()
        )
        if record is None:
            return None
        return record.payload

    def restore(self, db: Session, *, result_id: str, model: type[T]) -> T | None:
        """Deserialize a persisted payload into a Pydantic model."""
        payload = self.load_payload(db, result_id=result_id)
        if payload is None:
            return None
        try:
            return model.model_validate(payload)
        except ValidationError:
            return None

    def list_for_file(
        self,
        db: Session,
        *,
        file_id: int,
        result_type: str | None = None,
        limit: int = 20,
    ) -> list[ModelResult]:
        """Return recent persisted results for a file."""
        query = db.query(ModelResult).filter(ModelResult.file_id == file_id)
        if result_type is not None:
            query = query.filter(ModelResult.result_type == result_type)
        return query.order_by(ModelResult.created_at.desc()).limit(limit).all()


result_persistence_service = ResultPersistenceService()
