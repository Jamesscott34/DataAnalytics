"""Background job orchestration service."""

import threading
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.analysis_job import AnalysisJob, JobStatus
from app.schemas.jobs import JobCreateRequest, JobResponse
from app.services.quick_scan_service import quick_scan_service


class BackgroundJobError(ValueError):
    """Raised when a background job cannot be managed."""


class BackgroundJobService:
    """Create, run, cancel, and serialize analysis jobs."""

    def enqueue(
        self,
        db: Session,
        *,
        owner_id: int | None,
        request: JobCreateRequest,
        autostart: bool = True,
    ) -> JobResponse:
        """Persist a queued job and optionally start a worker thread."""
        job = AnalysisJob(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            job_type=request.job_type,
            status=JobStatus.QUEUED,
            progress=0,
            payload=request.payload,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        if autostart:
            threading.Thread(
                target=self._run_in_thread,
                args=(job.id,),
                name=f"analysis-job-{job.id}",
                daemon=True,
            ).start()
        return self.to_schema(job)

    def list_jobs(
        self, db: Session, *, owner_id: int | None, limit: int = 20
    ) -> list[JobResponse]:
        """Return recent jobs for the current user."""
        query = db.query(AnalysisJob)
        if owner_id is not None:
            query = query.filter(AnalysisJob.owner_id == owner_id)
        jobs = query.order_by(AnalysisJob.created_at.desc()).limit(limit).all()
        return [self.to_schema(job) for job in jobs]

    def get_job(
        self, db: Session, *, job_id: str, owner_id: int | None = None
    ) -> JobResponse:
        """Return a job by id."""
        job = self._get_job(db, job_id=job_id, owner_id=owner_id)
        return self.to_schema(job)

    def cancel(
        self, db: Session, *, job_id: str, owner_id: int | None = None
    ) -> JobResponse:
        """Cancel a queued or running job."""
        job = self._get_job(db, job_id=job_id, owner_id=owner_id)
        if job.status in {JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED}:
            return self.to_schema(job)
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        job.error = "Job cancelled by user"
        db.commit()
        db.refresh(job)
        return self.to_schema(job)

    def run_job(self, db: Session, *, job_id: str) -> JobResponse:
        """Run a queued job in the current process."""
        job = self._get_job(db, job_id=job_id)
        if job.status != JobStatus.QUEUED:
            return self.to_schema(job)

        try:
            self._mark_running(db, job)
            if self._is_cancelled(db, job.id):
                return self.get_job(db, job_id=job.id)

            if job.job_type == "quick_scan":
                self._set_progress(db, job, 25)
                file_id = int(job.payload.get("file_id", 0))
                report = quick_scan_service.run_quick_scan(db, file_id=file_id)
                self._complete(
                    db,
                    job,
                    result_id=report.report_id,
                    result={"report_id": report.report_id, "file_id": file_id},
                )
            elif job.job_type == "eda":
                from app.services.eda_service import eda_service

                file_id = int(job.payload.get("file_id", 0))
                force_refresh = bool(job.payload.get("force_refresh", False))
                self._set_progress(db, job, 20)
                if self._is_cancelled(db, job.id):
                    return self.get_job(db, job_id=job.id)
                self._set_progress(db, job, 50)
                response = eda_service.run_for_file(
                    db,
                    file_id=file_id,
                    force_refresh=force_refresh,
                )
                self._set_progress(db, job, 90)
                self._complete(
                    db,
                    job,
                    result_id=response.result_id,
                    result={
                        "file_id": file_id,
                        "result_id": response.result_id,
                        "row_count": response.summary.row_count,
                        "sampled": response.sampled,
                    },
                )
            elif job.job_type == "fail":
                raise BackgroundJobError(
                    str(job.payload.get("message") or "Job failed")
                )
            else:
                self._set_progress(db, job, 50)
                self._complete(db, job, result={"message": "Demo job complete"})
        except Exception as exc:  # noqa: BLE001 - job failures must be persisted.
            db.rollback()
            job = self._get_job(db, job_id=job_id)
            if job.status != JobStatus.CANCELLED:
                job.status = JobStatus.FAILED
                job.error = str(exc)
                job.completed_at = datetime.now(UTC)
                db.commit()
                db.refresh(job)
        return self.to_schema(job)

    def to_schema(self, job: AnalysisJob) -> JobResponse:
        """Serialize an ORM job."""
        return JobResponse(
            id=job.id,
            job_type=job.job_type,
            status=job.status.value,
            progress=job.progress,
            payload=job.payload,
            result=job.result,
            result_id=job.result_id,
            error=job.error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    def _run_in_thread(self, job_id: str) -> None:
        db = SessionLocal()
        try:
            self.run_job(db, job_id=job_id)
        finally:
            db.close()

    def _get_job(
        self,
        db: Session,
        *,
        job_id: str,
        owner_id: int | None = None,
    ) -> AnalysisJob:
        job = db.get(AnalysisJob, job_id)
        if job is None or (owner_id is not None and job.owner_id != owner_id):
            raise BackgroundJobError("Job not found")
        return job

    def _mark_running(self, db: Session, job: AnalysisJob) -> None:
        job.status = JobStatus.RUNNING
        job.progress = 10
        job.started_at = datetime.now(UTC)
        db.commit()
        db.refresh(job)

    def _set_progress(self, db: Session, job: AnalysisJob, progress: int) -> None:
        job.progress = progress
        db.commit()
        db.refresh(job)

    def _complete(
        self,
        db: Session,
        job: AnalysisJob,
        *,
        result: dict[str, object],
        result_id: str | None = None,
    ) -> None:
        if self._is_cancelled(db, job.id):
            return
        job.status = JobStatus.COMPLETE
        job.progress = 100
        job.result = result
        job.result_id = result_id
        job.completed_at = datetime.now(UTC)
        db.commit()
        db.refresh(job)

    def _is_cancelled(self, db: Session, job_id: str) -> bool:
        db.expire_all()
        job = self._get_job(db, job_id=job_id)
        return job.status == JobStatus.CANCELLED


background_job_service = BackgroundJobService()
