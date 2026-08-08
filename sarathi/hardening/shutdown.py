import asyncio
import time
from typing import Set

class ShutdownManager:
    def __init__(self, drain_timeout: float = 5.0):
        self.drain_timeout = drain_timeout
        self.is_shutting_down = False
        self.active_tasks: Set[asyncio.Task] = set()

    def track_task(self, task: asyncio.Task):
        self.active_tasks.add(task)
        task.add_done_callback(lambda t: self.active_tasks.discard(t))

    async def initiate_graceful_shutdown(self):
        self.is_shutting_down = True
        if not self.active_tasks:
            return

        start = time.monotonic()
        while self.active_tasks and (time.monotonic() - start) < self.drain_timeout:
            await asyncio.sleep(0.005)

        for task in list(self.active_tasks):
            if not task.done():
                task.cancel()
