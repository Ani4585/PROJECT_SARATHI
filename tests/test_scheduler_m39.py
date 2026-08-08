import pytest
import asyncio
from datetime import datetime, timezone
from sarathi.scheduler import (
    CronExpression, ScheduledJob, MisfirePolicy, TaskState,
    AsyncSchedulerEngine, DistributedLeaseLock
)

def test_cron_parsing_next_fire():
    cron = CronExpression("*/5 * * * *")
    now = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)
    nxt = cron.next_fire_time(from_time=now)
    assert nxt == datetime(2026, 8, 8, 12, 5, 0, tzinfo=timezone.utc)

@pytest.mark.asyncio
async def test_scheduler_job_execution():
    executed = []
    def sample_func(value):
        executed.append(value)

    engine = AsyncSchedulerEngine()
    job = ScheduledJob(name="test_job", func=sample_func, args=("m39_passed",), interval_seconds=10)
    job_id = engine.add_job(job)
    
    await engine.trigger_job(job_id)
    
    assert executed == ["m39_passed"]
    assert engine.jobs[job_id].run_count == 1

@pytest.mark.asyncio
async def test_lease_locking():
    lock = DistributedLeaseLock()
    acquired1 = await lock.acquire_lease("test_key", ttl_seconds=5)
    acquired2 = await lock.acquire_lease("test_key", ttl_seconds=5)
    
    assert acquired1 is True
    assert acquired2 is False
    
    await lock.release_lease("test_key")
    acquired3 = await lock.acquire_lease("test_key", ttl_seconds=5)
    assert acquired3 is True