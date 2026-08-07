"""Tests for ServiceLifetime.SCOPED and RequestScope."""

import asyncio
import pytest

from src.container import RequestScope, ServiceLifetime, ServiceScope, ScopeNotFoundError


class DisposableService:
    def __init__(self) -> None:
        self.disposed = False

    def dispose(self) -> None:
        self.disposed = True


class AsyncDisposableService:
    def __init__(self) -> None:
        self.disposed = False

    async def close(self) -> None:
        self.disposed = True


def test_request_scope_instance_caching() -> None:
    scope = RequestScope()
    assert scope.get("key") is None

    val = object()
    scope.set("key", val)
    assert scope.get("key") is val
    assert not scope.is_disposed


def test_request_scope_disposal_sync_and_async() -> None:
    async def run_test():
        scope = RequestScope()
        svc1 = DisposableService()
        svc2 = AsyncDisposableService()

        scope.set("svc1", svc1)
        scope.set("svc2", svc2)

        assert not svc1.disposed
        assert not svc2.disposed

        await scope.dispose()

        assert svc1.disposed
        assert svc2.disposed
        assert scope.is_disposed

    asyncio.run(run_test())


def test_request_scope_context_manager() -> None:
    async def run_test():
        svc = DisposableService()
        async with RequestScope() as scope:
            scope.set("svc", svc)

        assert svc.disposed

    asyncio.run(run_test())
