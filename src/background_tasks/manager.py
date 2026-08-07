from typing import Any, Callable, Dict, Optional
from .models import BackgroundTaskItem
from .queue import BackgroundTaskQueue
from .worker import BackgroundTaskWorker
from .scheduler import TaskScheduler
from src.async_runtime import IAsyncInitializer, IAsyncDisposable

class BackgroundTaskManager(IAsyncInitializer, IAsyncDisposable):
    def __init__(self, max_queue_size: int = 0) -> None:
        self.queue = BackgroundTaskQueue(maxsize=max_queue_size)
        self.worker = BackgroundTaskWorker(self.queue)
        self.scheduler = TaskScheduler(self.queue)
        self.task_registry: Dict[str, BackgroundTaskItem] = {}

    async def initialize_async(self) -> None:
        await self.worker.start()
        await self.scheduler.start()

    async def dispose_async(self) -> None:
        await self.scheduler.stop()
        await self.worker.stop()

    async def enqueue(self, func: Callable[..., Any], *args: Any, priority: int = 10, **kwargs: Any) -> str:
        item = BackgroundTaskItem(func=func, args=args, kwargs=kwargs, priority=priority)
        self.task_registry[item.task_id] = item
        await self.queue.enqueue(item)
        return item.task_id

    def schedule_periodic(self, func: Callable[..., Any], interval_seconds: float, *args: Any, **kwargs: Any) -> None:
        self.scheduler.schedule(func, interval_seconds, *args, **kwargs)

    def get_task(self, task_id: str) -> Optional[BackgroundTaskItem]:
        return self.task_registry.get(task_id)
