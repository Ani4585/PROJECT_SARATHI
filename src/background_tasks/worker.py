import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Optional
from .models import BackgroundTaskItem, TaskStatus
from .queue import BackgroundTaskQueue
from src.async_runtime import CancellationToken

logger = logging.getLogger("sarathi.background_tasks")

class BackgroundTaskWorker:
    def __init__(self, queue: BackgroundTaskQueue) -> None:
        self.queue = queue
        self._is_running = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self, cancellation_token: Optional[CancellationToken] = None) -> None:
        self._is_running = True
        self._worker_task = asyncio.create_task(self._run_loop(cancellation_token))

    async def stop(self) -> None:
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self, token: Optional[CancellationToken]) -> None:
        while self._is_running:
            if token and token.is_cancellation_requested:
                break
            try:
                item = await asyncio.wait_for(self.queue.dequeue(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            item.status = TaskStatus.RUNNING
            item.started_at = datetime.now(timezone.utc)
            try:
                if inspect.iscoroutinefunction(item.func):
                    item.result = await item.func(*item.args, **item.kwargs)
                else:
                    item.result = item.func(*item.args, **item.kwargs)
                item.status = TaskStatus.COMPLETED
            except Exception as ex:
                item.error = ex
                item.status = TaskStatus.FAILED
                logger.error(f"Task {item.task_id} failed: {ex}")
            finally:
                item.completed_at = datetime.now(timezone.utc)
                self.queue.task_done()
