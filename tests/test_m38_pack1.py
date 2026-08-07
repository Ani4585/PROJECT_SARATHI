import pytest
import asyncio
from src.background_tasks import (
    BackgroundTaskItem,
    BackgroundTaskQueue,
    BackgroundTaskWorker,
    TaskStatus
)

def test_background_task_execution():
    async def _test():
        queue = BackgroundTaskQueue()
        worker = BackgroundTaskWorker(queue)

        execution_flag = {"processed": False}

        async def sample_job(msg: str):
            execution_flag["processed"] = True
            return f"Processed: {msg}"

        item = BackgroundTaskItem(func=sample_job, args=("Hello Sarathi",))
        await queue.enqueue(item)

        await worker.start()
        await asyncio.sleep(0.15)
        await worker.stop()

        assert execution_flag["processed"] is True
        assert item.status == TaskStatus.COMPLETED
        assert item.result == "Processed: Hello Sarathi"

    asyncio.run(_test())
