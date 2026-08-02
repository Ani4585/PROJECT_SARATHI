"""Tests for the official M28 managed-resource framework."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest

from src.health import HealthStatus
from src.resources import (
    LazyResource,
    ResourceAcquisitionError,
    ResourceCleanupError,
    ResourceDefinition,
    ResourceLeakError,
    ResourceLifecycle,
    ResourcePool,
    ResourceRegistrationError,
    ResourceRegistry,
    ResourceRegistryHealthCheck,
    ResourceRegistryState,
    ResourceState,
    ResourceUnavailableError,
)


def test_resource_definition_validates_contract() -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        ResourceDefinition(" ", lambda: object())
    with pytest.raises(ValueError, match="depend on itself"):
        ResourceDefinition("database", lambda: object(), dependencies=("database",))
    with pytest.raises(ValueError, match="must be unique"):
        ResourceDefinition("app", lambda: object(), dependencies=("db", "db"))


def test_registry_rejects_duplicates_and_late_registration() -> None:
    registry = ResourceRegistry()
    registry.add("database", object)
    with pytest.raises(ResourceRegistrationError, match="already registered"):
        registry.add("database", object)
    registry.open()
    with pytest.raises(ResourceRegistrationError, match="after the registry starts"):
        registry.add("late", object)
    assert registry.close().passed is True


def test_registry_plan_is_deterministic_and_validates_graph() -> None:
    registry = ResourceRegistry()
    registry.add("web", object, dependencies=("cache", "database"))
    registry.add("database", object)
    registry.add("cache", object)
    assert registry.plan() == ("cache", "database", "web")

    missing = ResourceRegistry()
    missing.add("web", object, dependencies=("database",))
    with pytest.raises(ResourceRegistrationError, match="missing dependencies"):
        missing.plan()

    cyclic = ResourceRegistry()
    cyclic.add("first", object, dependencies=("second",))
    cyclic.add("second", object, dependencies=("first",))
    with pytest.raises(ResourceRegistrationError, match="cycle"):
        cyclic.plan()


def test_eager_resources_acquire_in_dependency_order_and_release_in_reverse() -> None:
    events: list[str] = []
    registry = ResourceRegistry()
    registry.add(
        "application",
        lambda: events.append("acquire:application") or "app",
        releaser=lambda value: events.append(f"release:{value}"),
        dependencies=("database",),
    )
    registry.add(
        "database",
        lambda: events.append("acquire:database") or "db",
        releaser=lambda value: events.append(f"release:{value}"),
    )
    registry.open()
    assert registry.get("application") == "app"
    report = registry.close()
    assert events == [
        "acquire:database",
        "acquire:application",
        "release:app",
        "release:db",
    ]
    assert report.released == ("application", "database")
    assert registry.close() is report


def test_registry_enters_and_exits_context_managed_resources() -> None:
    events: list[str] = []

    @contextmanager
    def connection():
        events.append("enter")
        yield "connected"
        events.append("exit")

    registry = ResourceRegistry()
    registry.add("connection", connection)
    with registry:
        assert registry.get("connection") == "connected"
    assert events == ["enter", "exit"]


def test_lazy_registry_resource_initializes_only_on_first_access() -> None:
    calls: list[str] = []
    registry = ResourceRegistry()
    registry.add("lazy", lambda: calls.append("acquire") or object(), lazy=True)
    registry.open()
    assert calls == []
    assert registry.snapshot().pending_lazy == 1
    first = registry.get("lazy")
    assert registry.get("lazy") is first
    assert calls == ["acquire"]
    registry.close()


def test_partial_open_rolls_back_already_acquired_resources() -> None:
    events: list[str] = []
    registry = ResourceRegistry()
    registry.add(
        "first",
        lambda: events.append("acquire:first") or "first",
        releaser=lambda value: events.append(f"release:{value}"),
    )

    def fail() -> object:
        events.append("acquire:second")
        raise RuntimeError("unavailable")

    registry.add("second", fail, dependencies=("first",))
    with pytest.raises(ResourceAcquisitionError, match="second"):
        registry.open()
    assert events == ["acquire:first", "acquire:second", "release:first"]
    assert registry.state is ResourceRegistryState.FAILED
    assert registry.snapshot().resources[0][1] is ResourceState.RELEASED


def test_cleanup_failures_are_isolated_and_reported() -> None:
    events: list[str] = []
    registry = ResourceRegistry()
    registry.add(
        "first",
        lambda: "first",
        releaser=lambda value: events.append(value),
    )

    def broken_release(value: object) -> None:
        events.append(str(value))
        raise RuntimeError("cleanup failed")

    registry.add("second", lambda: "second", releaser=broken_release)
    registry.open()
    report = registry.close()
    assert events == ["second", "first"]
    assert report.released == ("first",)
    assert report.failures[0].resource == "second"
    assert "cleanup failed" in report.failures[0].message


def test_context_manager_raises_cleanup_error_without_masking_body_errors() -> None:
    registry = ResourceRegistry()
    registry.add(
        "broken",
        object,
        releaser=lambda value: (_ for _ in ()).throw(RuntimeError("close")),
    )
    with pytest.raises(ResourceCleanupError, match="cleanup failed"):
        with registry:
            pass

    second = ResourceRegistry()
    second.add(
        "broken",
        object,
        releaser=lambda value: (_ for _ in ()).throw(RuntimeError("close")),
    )
    with pytest.raises(ValueError, match="body"):
        with second:
            raise ValueError("body")


def test_registry_rejects_access_when_closed_or_unknown() -> None:
    registry = ResourceRegistry()
    registry.add("known", object)
    with pytest.raises(ResourceUnavailableError, match="not open"):
        registry.get("known")
    registry.open()
    with pytest.raises(ResourceUnavailableError, match="not registered"):
        registry.get("missing")
    registry.close()
    with pytest.raises(ResourceUnavailableError, match="not open"):
        registry.get("known")


def test_lifecycle_and_health_adapters_reflect_registry_state() -> None:
    registry = ResourceRegistry()
    registry.add("eager", object)
    registry.add("optional", object, lazy=True)
    lifecycle = ResourceLifecycle(registry)
    health = ResourceRegistryHealthCheck(registry)
    assert lifecycle.running is False
    assert health.run().status is HealthStatus.UNHEALTHY
    lifecycle.start()
    result = health.run()
    assert lifecycle.running is True
    assert result.status is HealthStatus.HEALTHY
    assert "Pending lazy: 1" in result.details
    assert lifecycle.stop().passed is True


def test_lazy_resource_is_thread_safe_and_closes_once() -> None:
    calls: list[str] = []
    lazy = LazyResource(
        lambda: calls.append("create") or object(),
        lambda value: calls.append("close"),
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        values = tuple(executor.map(lambda _: lazy.get(), range(20)))
    assert all(value is values[0] for value in values)
    assert calls == ["create"]
    lazy.close()
    lazy.close()
    assert calls == ["create", "close"]


def test_lazy_resource_records_acquisition_and_cleanup_failures() -> None:
    failing = LazyResource(lambda: (_ for _ in ()).throw(RuntimeError("create")))
    with pytest.raises(ResourceAcquisitionError, match="create"):
        failing.get()
    assert failing.state is ResourceState.FAILED

    cleanup = LazyResource(
        object,
        lambda value: (_ for _ in ()).throw(RuntimeError("close")),
    )
    cleanup.get()
    with pytest.raises(ResourceCleanupError, match="close"):
        cleanup.close()
    assert cleanup.state is ResourceState.FAILED


def test_pool_enforces_capacity_timeout_and_reuses_resources() -> None:
    created: list[object] = []

    def factory() -> object:
        value = object()
        created.append(value)
        return value

    pool = ResourcePool(factory, max_size=2, min_size=1).open()
    first = pool.acquire()
    second = pool.acquire()
    with pytest.raises(ResourceAcquisitionError, match="Timed out"):
        pool.acquire(timeout=0)
    first_value = first.value
    first.release()
    third = pool.acquire(timeout=0)
    assert third.value is first_value
    second.release()
    third.release()
    assert pool.snapshot().available == 2
    pool.close()


def test_invalidated_pool_lease_is_discarded_and_replaced() -> None:
    released: list[object] = []
    pool = ResourcePool(object, released.append, max_size=1).open()
    lease = pool.acquire()
    discarded = lease.value
    lease.invalidate()
    lease.release()
    assert released == [discarded]
    replacement = pool.acquire()
    assert replacement.value is not discarded
    replacement.release()
    pool.close()


def test_pool_detects_unreleased_leases_before_shutdown() -> None:
    pool = ResourcePool(object, max_size=1).open()
    lease = pool.acquire()
    with pytest.raises(ResourceLeakError, match="1 unreleased"):
        pool.close()
    assert pool.snapshot().open is True
    lease.release()
    pool.close()
    assert pool.snapshot().open is False


def test_pool_warmup_failure_rolls_back_partial_initialization() -> None:
    attempts = 0
    released: list[object] = []

    def factory() -> object:
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise RuntimeError("warmup")
        return object()

    pool = ResourcePool(factory, released.append, max_size=2, min_size=2)
    with pytest.raises(ResourceAcquisitionError, match="warm-up"):
        pool.open()
    assert len(released) == 1
    assert pool.snapshot().open is False


def test_pool_can_be_owned_and_cleaned_by_resource_registry() -> None:
    registry = ResourceRegistry()
    registry.add("pool", lambda: ResourcePool(object, max_size=2).open())
    with registry:
        pool = registry.get("pool")
        assert isinstance(pool, ResourcePool)
        with pool.acquire() as value:
            assert value is not None
    assert pool.snapshot().open is False
