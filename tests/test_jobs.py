"""Tests for the M18 background job engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.jobs import Job, JobScheduler, JobStatus


NOW = datetime(2026, 8, 1, 18, 0, tzinfo=UTC)


def test_job_validates_definition() -> None:
    with pytest.raises(ValueError):
        Job(" ", lambda: None, NOW)
    with pytest.raises(ValueError):
        Job("job", lambda: None, NOW, max_attempts=0)
    with pytest.raises(ValueError):
        Job("job", lambda: None, datetime.now())


def test_scheduler_rejects_duplicate_job_identity() -> None:
    scheduler = JobScheduler()
    job = Job("job", lambda: None, NOW)
    scheduler.schedule(job)
    with pytest.raises(ValueError):
        scheduler.schedule(job)


def test_scheduler_returns_only_due_jobs() -> None:
    scheduler = JobScheduler(lambda: NOW)
    due = Job("due", lambda: None, NOW)
    later = Job("later", lambda: None, NOW + timedelta(hours=1))
    scheduler.schedule(later)
    scheduler.schedule(due)
    assert tuple(record.job.name for record in scheduler.due()) == ("due",)


def test_due_jobs_are_ordered_by_time_then_insertion() -> None:
    scheduler = JobScheduler(lambda: NOW)
    scheduler.schedule(Job("second-time", lambda: None, NOW))
    scheduler.schedule(Job("first-time", lambda: None, NOW - timedelta(minutes=1)))
    scheduler.schedule(Job("same-time", lambda: None, NOW))
    assert tuple(record.job.name for record in scheduler.due()) == (
        "first-time",
        "second-time",
        "same-time",
    )


def test_scheduler_runs_due_job_and_records_result() -> None:
    scheduler = JobScheduler(lambda: NOW)
    job_id = scheduler.schedule(Job("answer", lambda: 42, NOW))
    execution = scheduler.run_due()[0]
    assert execution.result == 42
    assert execution.status is JobStatus.SUCCEEDED
    assert scheduler.get(job_id).attempts == 1
    assert scheduler.run_due() == ()


def test_scheduler_isolates_failed_jobs_and_continues() -> None:
    calls: list[str] = []

    def broken() -> None:
        raise RuntimeError("boom")

    scheduler = JobScheduler(lambda: NOW)
    scheduler.schedule(Job("broken", broken, NOW))
    scheduler.schedule(Job("working", lambda: calls.append("working"), NOW))
    executions = scheduler.run_due()
    assert [execution.status for execution in executions] == [
        JobStatus.FAILED,
        JobStatus.SUCCEEDED,
    ]
    assert executions[0].error == "RuntimeError: boom"
    assert calls == ["working"]


def test_scheduler_retries_after_declared_delay() -> None:
    attempts = 0

    def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("retry")
        return "done"

    scheduler = JobScheduler(lambda: NOW)
    job_id = scheduler.schedule(
        Job("flaky", flaky, NOW, max_attempts=2, retry_delay=timedelta(minutes=5))
    )
    first = scheduler.run_due()[0]
    assert first.status is JobStatus.RETRY_SCHEDULED
    assert scheduler.get(job_id).next_run_at == NOW + timedelta(minutes=5)
    assert scheduler.run_due(NOW + timedelta(minutes=4)) == ()
    second = scheduler.run_due(NOW + timedelta(minutes=5))[0]
    assert second.status is JobStatus.SUCCEEDED
    assert second.result == "done"


def test_scheduler_stops_retrying_at_attempt_limit() -> None:
    scheduler = JobScheduler(lambda: NOW)
    job_id = scheduler.schedule(
        Job("broken", lambda: 1 / 0, NOW, max_attempts=2)
    )
    scheduler.run_due()
    scheduler.run_due()
    record = scheduler.get(job_id)
    assert record.status is JobStatus.FAILED
    assert record.attempts == 2
    assert record.next_run_at is None


def test_scheduler_cancels_pending_job() -> None:
    scheduler = JobScheduler(lambda: NOW)
    job_id = scheduler.schedule(Job("job", lambda: None, NOW))
    assert scheduler.cancel(job_id) is True
    assert scheduler.cancel(job_id) is False
    assert scheduler.get(job_id).status is JobStatus.CANCELLED
    assert scheduler.run_due() == ()


def test_scheduler_cannot_cancel_completed_job() -> None:
    scheduler = JobScheduler(lambda: NOW)
    job_id = scheduler.schedule(Job("job", lambda: None, NOW))
    scheduler.run_due()
    assert scheduler.cancel(job_id) is False


def test_scheduler_rejects_naive_current_time() -> None:
    with pytest.raises(ValueError):
        JobScheduler().due(datetime.now())
