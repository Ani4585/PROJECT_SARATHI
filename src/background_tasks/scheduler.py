import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from .models import BackgroundTaskItem
from .queue import BackgroundTaskQueue

class ScheduledTask:
    def __init__(self, func: Callable[..., Any], interval_seconds: float, args: tuple = (), kwargs: Optional[Dict[str, Any]] = None):
        self.func = func
        self.interval_seconds = interval_seconds
        self.args = args
        self.kwargs = kwargs or {}
        self.last_run: Optional[datetime] = None

class TaskScheduler:
    def __init__(self, queue: BackgroundTaskQueue) -> None:
        self.queue = queue
        self.scheduled_tasks: List[ScheduledTask] = []
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    def schedule(self, func: Callable[..., Any], interval_seconds: float, *args: Any, **kwargs: Any) -> ScheduledTask:
        task = ScheduledTask(func, interval_seconds, args=args, kwargs=kwargs)
        self.scheduled_tasks.append(task)
        return task

    async def start(self) -> None:
        self._is_running = True
        self._loop_task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self) -> None:
        while self._is_running:
            now = datetime.now(timezone.utc)
            for st in self.scheduled_tasks:
                if st.last_run is None or (now - st.last_run).total_seconds() >= st.interval_seconds:
                    st.last_run = now
                    item = BackgroundTaskItem(func=st.func, args=st.args, kwargs=st.kwargs)
                    await self.queue.enqueue(item)
            await asyncio.sleep(0.05)
