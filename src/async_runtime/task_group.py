import asyncio
import sys
from typing import Any, Coroutine, Optional, Set

class TaskGroup:
    def __init__(self) -> None:
        self._tasks: Set[asyncio.Task] = set()
        self._tg: Optional[Any] = None
        self._is_closed: bool = False

    async def __aenter__(self) -> "TaskGroup":
        if sys.version_info >= (3, 11):
            self._tg = asyncio.TaskGroup()
            await self._tg.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Optional[bool]:
        if self._tg is not None:
            return await self._tg.__aexit__(exc_type, exc_val, exc_tb)
        
        self._is_closed = True
        if not self._tasks:
            return None

        try:
            if exc_type is not None:
                for task in self._tasks:
                    if not task.done():
                        task.cancel()
            
            results = await asyncio.gather(*self._tasks, return_exceptions=True)
            if exc_type is None:
                for res in results:
                    if isinstance(res, Exception) and not isinstance(res, asyncio.CancelledError):
                        raise res
        finally:
            self._tasks.clear()
        return None

    def create_task(self, coro: Coroutine[Any, Any, Any], name: Optional[str] = None) -> asyncio.Task:
        if self._tg is not None:
            return self._tg.create_task(coro, name=name)
        
        if self._is_closed:
            raise RuntimeError("TaskGroup is closed and cannot accept new tasks.")

        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def cancel_all(self) -> None:
        if self._tg is not None and hasattr(self._tg, "_tasks"):
            for t in getattr(self._tg, "_tasks", []):
                t.cancel()
        else:
            for task in list(self._tasks):
                if not task.done():
                    task.cancel()
