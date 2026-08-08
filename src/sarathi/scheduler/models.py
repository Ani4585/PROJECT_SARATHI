import dataclasses
import uuid
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable, Any, Dict, Optional

class MisfirePolicy(Enum):
    FIRE_IMMEDIATELY = auto()
    SKIP = auto()
    RESCHEDULE_NEXT = auto()

class TaskState(Enum):
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclasses.dataclass
class ScheduledJob:
    job_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Optional[Callable[..., Any]] = None
    args: tuple = dataclasses.field(default_factory=tuple)
    kwargs: Dict[str, Any] = dataclasses.field(default_factory=dict)
    cron_expr: Optional[str] = None
    interval_seconds: Optional[float] = None
    misfire_policy: MisfirePolicy = MisfirePolicy.SKIP
    misfire_grace_period: float = 60.0
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    state: TaskState = TaskState.PENDING
    max_runs: Optional[int] = None
    run_count: int = 0