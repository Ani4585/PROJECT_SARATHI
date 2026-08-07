import asyncio
from typing import Optional, Tuple
from .models import BackgroundTaskItem

class BackgroundTaskQueue:
    def __init__(self, maxsize: int = 0) -> None:
        self._queue: asyncio.PriorityQueue[Tuple[int, BackgroundTaskItem]] = asyncio.PriorityQueue(maxsize=maxsize)

    async def enqueue(self, item: BackgroundTaskItem) -> str:
        await self._queue.put((item.priority, item))
        return item.task_id

    async def dequeue(self) -> BackgroundTaskItem:
        priority, item = await self._queue.get()
        return item

    def task_done(self) -> None:
        self._queue.task_done()

    @property
    def size(self) -> int:
        return self._queue.qsize()
