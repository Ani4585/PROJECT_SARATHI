"""Deterministic in-process background job scheduler."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from threading import RLock
from uuid import UUID

from .job import Job, JobExecution, JobRecord, JobStatus


Clock = Callable[[], datetime]


class JobScheduler:
    """Schedule and execute due work in stable insertion order."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._records: dict[UUID, JobRecord] = {}
        self._sequence: dict[UUID, int] = {}
        self._next_sequence = 0
        self._lock = RLock()

    def schedule(self, job: Job) -> UUID:
        with self._lock:
            if job.job_id in self._records:
                raise ValueError(f"Job {job.job_id} is already scheduled.")
            self._records[job.job_id] = JobRecord(job)
            self._sequence[job.job_id] = self._next_sequence
            self._next_sequence += 1
            return job.job_id

    def get(self, job_id: UUID) -> JobRecord:
        try:
            return self._records[job_id]
        except KeyError as error:
            raise KeyError(f"Job {job_id} is not scheduled.") from error

    def cancel(self, job_id: UUID) -> bool:
        with self._lock:
            record = self.get(job_id)
            if record.status in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}:
                return False
            record.status = JobStatus.CANCELLED
            record.next_run_at = None
            return True

    def due(self, at: datetime | None = None) -> tuple[JobRecord, ...]:
        current = at or self._clock()
        if current.tzinfo is None:
            raise ValueError("Scheduler time must be timezone-aware.")
        eligible = (
            record
            for record in self._records.values()
            if record.status in {JobStatus.PENDING, JobStatus.RETRY_SCHEDULED}
            and record.next_run_at is not None
            and record.next_run_at <= current
        )
        return tuple(
            sorted(
                eligible,
                key=lambda record: (
                    record.next_run_at,
                    self._sequence[record.job.job_id],
                ),
            )
        )

    def run_due(self, at: datetime | None = None) -> tuple[JobExecution, ...]:
        current = at or self._clock()
        executions: list[JobExecution] = []
        with self._lock:
            for record in self.due(current):
                record.status = JobStatus.RUNNING
                record.attempts += 1
                record.error = None
                try:
                    result = record.job.action()
                except Exception as error:
                    record.error = f"{type(error).__name__}: {error}"
                    if record.attempts < record.job.max_attempts:
                        record.status = JobStatus.RETRY_SCHEDULED
                        record.next_run_at = current + record.job.retry_delay
                    else:
                        record.status = JobStatus.FAILED
                        record.next_run_at = None
                else:
                    record.status = JobStatus.SUCCEEDED
                    record.result = result
                    record.next_run_at = None
                executions.append(
                    JobExecution(
                        job_id=record.job.job_id,
                        name=record.job.name,
                        attempt=record.attempts,
                        status=record.status,
                        result=record.result,
                        error=record.error,
                    )
                )
        return tuple(executions)

    @property
    def records(self) -> tuple[JobRecord, ...]:
        return tuple(self._records.values())
