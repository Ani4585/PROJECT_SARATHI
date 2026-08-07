import pytest
import asyncio
from src.async_runtime import (
    IAsyncInitializer,
    IAsyncDisposable,
    TaskGroup,
    AsyncContainerLifecycleManager
)

class MockDatabaseService(IAsyncInitializer, IAsyncDisposable):
    def __init__(self):
        self.is_initialized = False
        self.is_disposed = False

    async def initialize_async(self) -> None:
        await asyncio.sleep(0.01)
        self.is_initialized = True

    async def dispose_async(self) -> None:
        await asyncio.sleep(0.01)
        self.is_disposed = True

def test_container_lifecycle_manager():
    async def _test():
        manager = AsyncContainerLifecycleManager()
        db = manager.register_instance(MockDatabaseService())
        
        assert not db.is_initialized
        assert not db.is_disposed

        async with manager:
            assert db.is_initialized
            assert not db.is_disposed

        assert db.is_disposed

    asyncio.run(_test())

def test_task_group_concurrency():
    async def _test():
        results = []

        async def sample_worker(val: int):
            await asyncio.sleep(0.01)
            results.append(val)

        async with TaskGroup() as tg:
            tg.create_task(sample_worker(1))
            tg.create_task(sample_worker(2))
            tg.create_task(sample_worker(3))

        assert sorted(results) == [1, 2, 3]

    asyncio.run(_test())

def test_task_group_cancellation():
    async def _test():
        cancelled_count = 0

        async def long_running():
            nonlocal cancelled_count
            try:
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                cancelled_count += 1
                raise

        with pytest.raises(Exception):
            async with TaskGroup() as tg:
                tg.create_task(long_running())
                tg.create_task(long_running())
                tg.cancel_all()
                raise RuntimeError("Force exit")

    asyncio.run(_test())
