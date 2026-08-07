"""Tests for Async Runtime Integration, Cancellation, Timeouts, and Sync/Async Bridges."""

import asyncio
import time
import pytest

from src.async_runtime import (
    CancellationToken,
    IAsyncDisposable,
    IAsyncInitializer,
    run_in_thread,
    run_sync,
    with_timeout,
)


class SampleAsyncService(IAsyncInitializer, IAsyncDisposable):
    def __init__(self) -> None:
        self.initialized = False
        self.disposed = False

    async def initialize(self) -> None:
        await asyncio.sleep(0.01)
        self.initialized = True

    async def dispose(self) -> None:
        await asyncio.sleep(0.01)
        self.disposed = True


def test_async_service_protocols() -> None:
    svc = SampleAsyncService()
    assert isinstance(svc, IAsyncInitializer)
    assert isinstance(svc, IAsyncDisposable)

    async def run_lifecycle():
        await svc.initialize()
        assert svc.initialized
        await svc.dispose()
        assert svc.disposed

    asyncio.run(run_lifecycle())


def test_cancellation_token() -> None:
    token = CancellationToken()
    assert not token.is_cancellation_requested

    token.cancel()
    assert token.is_cancellation_requested

    with pytest.raises(asyncio.CancelledError):
        token.throwIfCancellationRequested()


def test_with_timeout_enforcement() -> None:
    async def fast_op():
        return "ok"

    async def slow_op():
        await asyncio.sleep(0.5)
        return "slow"

    assert asyncio.run(with_timeout(fast_op(), 0.1)) == "ok"

    with pytest.raises(TimeoutError, match="timed out after 0.05 seconds"):
        asyncio.run(with_timeout(slow_op(), 0.05))


def test_run_in_thread_blocking_boundary() -> None:
    def blocking_work(x: int, y: int) -> int:
        time.sleep(0.02)
        return x + y

    async def main():
        result = await run_in_thread(blocking_work, 10, 20)
        assert result == 30

    asyncio.run(main())


def test_run_sync_from_sync_context() -> None:
    async def sample_coro():
        return 42

    result = run_sync(sample_coro())
    assert result == 42
