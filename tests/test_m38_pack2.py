import pytest
import asyncio
from src.background_tasks import BackgroundTaskManager, TaskStatus
from src.async_runtime import AsyncContainerLifecycleManager

def test_background_task_manager_and_scheduler():
    async def _test():
        manager = BackgroundTaskManager()
        lifecycle = AsyncContainerLifecycleManager()
        lifecycle.register_instance(manager)

        executed_count = 0

        async def periodic_job():
            nonlocal executed_count
            executed_count += 1

        manager.schedule_periodic(periodic_job, interval_seconds=0.05)

        async with lifecycle:
            task_id = await manager.enqueue(lambda x, y: x + y, 5, 10)
            await asyncio.sleep(0.2)

            item = manager.get_task(task_id)
            assert item is not None
            assert item.status == TaskStatus.COMPLETED
            assert item.result == 15
            assert executed_count >= 2

    asyncio.run(_test())
