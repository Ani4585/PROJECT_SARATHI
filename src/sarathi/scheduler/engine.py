import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from .cron import CronExpression
from .models import ScheduledJob, MisfirePolicy, TaskState

logger = logging.getLogger("sarathi.scheduler")

class DistributedLeaseLock:
    def __init__(self):
        self._locks: Dict[str, datetime] = {}

    async def acquire_lease(self, lock_key: str, ttl_seconds: float = 10.0) -> bool:
        now = datetime.now(timezone.utc)
        if lock_key in self._locks:
            if self._locks[lock_key] > now:
                return False
        self._locks[lock_key] = now + timedelta(seconds=ttl_seconds)
        return True

    async def release_lease(self, lock_key: str):
        self._locks.pop(lock_key, None)

class AsyncSchedulerEngine:
    def __init__(self, lease_lock: Optional[DistributedLeaseLock] = None):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.lease_lock = lease_lock or DistributedLeaseLock()
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None

    def add_job(self, job: ScheduledJob) -> str:
        if job.cron_expr:
            cron = CronExpression(job.cron_expr)
            job.next_run_at = cron.next_fire_time()
        elif job.interval_seconds:
            job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)
        
        self.jobs[job.job_id] = job
        logger.info(f"Job registered: {job.name} ({job.job_id})")
        return job.job_id

    async def trigger_job(self, job_id: str):
        if job_id in self.jobs:
            now = datetime.now(timezone.utc)
            await self._process_job(self.jobs[job_id], now)

    async def _process_job(self, job: ScheduledJob, now: datetime):
        lock_acquired = await self.lease_lock.acquire_lease(f"job_lock:{job.job_id}")
        if not lock_acquired:
            return

        try:
            job.state = TaskState.RUNNING
            job.last_run_at = now
            job.run_count += 1
            
            if asyncio.iscoroutinefunction(job.func):
                await job.func(*job.args, **job.kwargs)
            elif job.func:
                job.func(*job.args, **job.kwargs)

            job.state = TaskState.PENDING
        except Exception as e:
            job.state = TaskState.FAILED
            raise e
        finally:
            await self.lease_lock.release_lease(f"job_lock:{job.job_id}")
            self._schedule_next_run(job)

    def _schedule_next_run(self, job: ScheduledJob):
        if job.max_runs and job.run_count >= job.max_runs:
            job.state = TaskState.COMPLETED
            return

        if job.cron_expr:
            cron = CronExpression(job.cron_expr)
            job.next_run_at = cron.next_fire_time(from_time=datetime.now(timezone.utc))
        elif job.interval_seconds:
            job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)