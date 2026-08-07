import asyncio
import concurrent.futures
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")

async def with_timeout(coro: Coroutine[Any, Any, T], timeout_seconds: float) -> T:
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except (asyncio.TimeoutError, TimeoutError):
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")

async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

def run_sync(coro: Coroutine[Any, Any, T]) -> T:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)
