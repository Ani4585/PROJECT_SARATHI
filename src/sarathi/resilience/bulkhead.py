import asyncio
import functools
import inspect
from typing import Callable, Optional, Any

class BulkheadFullException(Exception):
    """Raised when bulkhead concurrent capacity and queuing capacity are both exhausted."""
    pass

class Bulkhead:
    def __init__(self, max_concurrent: int = 10, max_queued: int = 10, name: str = "default"):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_queued = max_queued
        self._active_calls = 0
        self._queued_calls = 0
        self._async_lock: Optional[asyncio.Lock] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

        self.metrics = {
            "accepted": 0,
            "rejected": 0,
            "active": 0,
            "queued": 0
        }

    def _init_async(self):
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

    async def execute_async(self, func: Callable, *args, **kwargs):
        self._init_async()
        async with self._async_lock:
            if self._active_calls >= self.max_concurrent:
                if self._queued_calls >= self.max_queued:
                    self.metrics["rejected"] += 1
                    raise BulkheadFullException(
                        f"Bulkhead '{self.name}' full: active={self._active_calls}, queued={self._queued_calls}"
                    )
                self._queued_calls += 1
                self.metrics["queued"] = self._queued_calls
                is_queued = True
            else:
                is_queued = False

        try:
            async with self._semaphore:
                async with self._async_lock:
                    if is_queued:
                        self._queued_calls -= 1
                        self.metrics["queued"] = self._queued_calls
                    self._active_calls += 1
                    self.metrics["accepted"] += 1
                    self.metrics["active"] = self._active_calls

                try:
                    res = func(*args, **kwargs)
                    if inspect.iscoroutine(res) or asyncio.iscoroutinefunction(func):
                        res = await res
                    return res
                finally:
                    async with self._async_lock:
                        self._active_calls -= 1
                        self.metrics["active"] = self._active_calls
        except BulkheadFullException:
            raise
        except Exception:
            raise

    def execute_sync(self, func: Callable, *args, **kwargs):
        if self._active_calls >= self.max_concurrent:
            if self._queued_calls >= self.max_queued:
                self.metrics["rejected"] += 1
                raise BulkheadFullException(
                    f"Bulkhead '{self.name}' full: active={self._active_calls}, queued={self._queued_calls}"
                )
        self._active_calls += 1
        self.metrics["accepted"] += 1
        self.metrics["active"] = self._active_calls
        try:
            return func(*args, **kwargs)
        finally:
            self._active_calls -= 1
            self.metrics["active"] = self._active_calls

    def __call__(self, func: Callable):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute_async(func, *args, **kwargs)
            return wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute_sync(func, *args, **kwargs)
            return wrapper

def bulkhead(max_concurrent: int = 10, max_queued: int = 10, name: str = "default"):
    bh = Bulkhead(max_concurrent=max_concurrent, max_queued=max_queued, name=name)
    def decorator(fn):
        return bh(fn)
    return decorator
