"""Background job definitions and execution records."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4


JobAction = Callable[[], object]


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class Job:
    """Immutable background work definition."""

    name: str
    action: JobAction
    scheduled_for: datetime
    max_attempts: int = 1
    retry_delay: timedelta = timedelta()
    job_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Job name must not be blank.")
        if not callable(self.action):
            raise TypeError("Job action must be callable.")
        if self.scheduled_for.tzinfo is None:
            raise ValueError("Job schedule must be timezone-aware.")
        if self.max_attempts < 1:
            raise ValueError("Job max_attempts must be at least one.")
        if self.retry_delay < timedelta():
            raise ValueError("Job retry_delay must not be negative.")


@dataclass(slots=True)
class JobRecord:
    """Mutable runtime state for one immutable job definition."""

    job: Job
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    next_run_at: datetime | None = None
    result: object = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.next_run_at is None:
            self.next_run_at = self.job.scheduled_for


@dataclass(frozen=True, slots=True)
class JobExecution:
    """Describe one scheduler execution attempt."""

    job_id: UUID
    name: str
    attempt: int
    status: JobStatus
    result: object = None
    error: str | None = None
