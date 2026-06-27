"""Background job service tests."""

from sqlalchemy.orm import Session

from app.models.analysis_job import AnalysisJob, JobStatus
from app.schemas.jobs import JobCreateRequest
from app.services.background_service import background_job_service


def test_background_job_runs_queued_to_complete(db_session: Session) -> None:
    """A queued demo job transitions to complete with progress."""
    response = background_job_service.enqueue(
        db_session,
        owner_id=1,
        request=JobCreateRequest(job_type="demo"),
        autostart=False,
    )

    queued = db_session.get(AnalysisJob, response.id)
    assert queued is not None
    assert queued.status == JobStatus.QUEUED

    completed = background_job_service.run_job(db_session, job_id=response.id)

    assert completed.status == "complete"
    assert completed.progress == 100
    assert completed.started_at is not None
    assert completed.completed_at is not None
    assert completed.result == {"message": "Demo job complete"}


def test_background_job_cancel_stops_queued_job(db_session: Session) -> None:
    """Queued jobs can be cancelled before execution."""
    response = background_job_service.enqueue(
        db_session,
        owner_id=1,
        request=JobCreateRequest(job_type="demo"),
        autostart=False,
    )

    cancelled = background_job_service.cancel(
        db_session, job_id=response.id, owner_id=1
    )
    rerun = background_job_service.run_job(db_session, job_id=response.id)

    assert cancelled.status == "cancelled"
    assert rerun.status == "cancelled"
    assert rerun.error == "Job cancelled by user"


def test_background_job_failed_stores_error(db_session: Session) -> None:
    """Failed jobs persist the error message."""
    response = background_job_service.enqueue(
        db_session,
        owner_id=1,
        request=JobCreateRequest(
            job_type="fail",
            payload={"message": "synthetic failure"},
        ),
        autostart=False,
    )

    failed = background_job_service.run_job(db_session, job_id=response.id)

    assert failed.status == "failed"
    assert failed.error == "synthetic failure"
    assert failed.completed_at is not None
