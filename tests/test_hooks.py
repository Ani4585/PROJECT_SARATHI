"""Tests for the official M22 hook system."""

from __future__ import annotations

import asyncio

import pytest

from src.hooks import HookDecision, HookEvent, HookRegistry, HookStatus


def test_event_payload_is_immutable() -> None:
    event = HookEvent("before.start", {"value": 1})
    with pytest.raises(TypeError):
        event.payload["value"] = 2  # type: ignore[index]


def test_registry_orders_handlers_by_priority_then_owner() -> None:
    calls: list[str] = []
    registry = HookRegistry()
    registry.register("event", lambda event: calls.append("low"), owner="low", priority=1)
    registry.register("event", lambda event: calls.append("beta"), owner="beta", priority=10)
    registry.register("event", lambda event: calls.append("alpha"), owner="alpha", priority=10)
    report = registry.dispatch(HookEvent("event", {}))
    assert calls == ["alpha", "beta", "low"]
    assert report.passed is True


def test_duplicate_owner_is_rejected_and_unregister_is_safe() -> None:
    registry = HookRegistry()
    registry.register("event", lambda event: None, owner="plugin")
    with pytest.raises(ValueError, match="already registered"):
        registry.register("event", lambda event: None, owner="plugin")
    assert registry.unregister("event", "missing") is False
    assert registry.unregister("event", "plugin") is True
    assert registry.registrations("event") == ()


def test_filter_skips_handler() -> None:
    calls: list[str] = []
    registry = HookRegistry()
    registry.register(
        "event",
        lambda event: calls.append("called"),
        owner="filtered",
        predicate=lambda event: False,
    )
    report = registry.dispatch(HookEvent("event", {}))
    assert calls == []
    assert report.outcomes[0].status is HookStatus.SKIPPED


def test_cancellation_stops_remaining_handlers() -> None:
    calls: list[str] = []
    registry = HookRegistry()
    registry.register(
        "event",
        lambda event: (calls.append("cancel"), HookDecision.CANCEL)[1],
        owner="cancel",
        priority=10,
    )
    registry.register("event", lambda event: calls.append("later"), owner="later")
    report = registry.dispatch(HookEvent("event", {}))
    assert calls == ["cancel"]
    assert report.cancelled is True
    assert report.outcomes[0].status is HookStatus.CANCELLED


def test_handler_and_filter_failures_are_isolated() -> None:
    calls: list[str] = []
    registry = HookRegistry()
    registry.register(
        "event",
        lambda event: None,
        owner="bad-filter",
        priority=20,
        predicate=lambda event: (_ for _ in ()).throw(ValueError("filter failed")),
    )
    registry.register(
        "event",
        lambda event: (_ for _ in ()).throw(RuntimeError("handler failed")),
        owner="bad-handler",
        priority=10,
    )
    registry.register("event", lambda event: calls.append("working"), owner="working")
    report = registry.dispatch(HookEvent("event", {}))
    assert calls == ["working"]
    assert report.failures == 2
    assert "ValueError: filter failed" in (report.outcomes[0].message or "")
    assert "RuntimeError: handler failed" in (report.outcomes[1].message or "")


def test_execution_is_instrumented_with_duration() -> None:
    readings = iter((1.0, 1.25))
    events = []
    registry = HookRegistry(clock=lambda: next(readings), observer=events.append)
    registry.register("event", lambda event: None, owner="plugin")
    report = registry.dispatch(HookEvent("event", {}))
    assert report.outcomes[0].duration_seconds == 0.25
    assert events[0].hook == "event"
    assert events[0].owner == "plugin"
    assert events[0].duration_seconds == 0.25


def test_observer_failure_does_not_fail_hook() -> None:
    registry = HookRegistry(observer=lambda event: (_ for _ in ()).throw(RuntimeError("sink")))
    registry.register("event", lambda event: None, owner="plugin")
    assert registry.dispatch(HookEvent("event", {})).passed is True


def test_sync_dispatch_reports_async_handler_without_leaking_coroutine() -> None:
    async def handler(event: HookEvent) -> None:
        del event

    registry = HookRegistry()
    registry.register("event", handler, owner="async")
    report = registry.dispatch(HookEvent("event", {}))
    assert report.failures == 1
    assert "requires dispatch_async" in (report.outcomes[0].message or "")


def test_async_dispatch_supports_sync_and_async_handlers_and_filters() -> None:
    calls: list[str] = []

    async def selected(event: HookEvent) -> bool:
        return event.payload["enabled"] is True

    async def async_handler(event: HookEvent) -> None:
        calls.append(f"async:{event.payload['value']}")

    registry = HookRegistry()
    registry.register("event", async_handler, owner="async", priority=10, predicate=selected)
    registry.register("event", lambda event: calls.append("sync"), owner="sync")
    report = asyncio.run(registry.dispatch_async(HookEvent("event", {"enabled": True, "value": 7})))
    assert calls == ["async:7", "sync"]
    assert report.passed is True


def test_async_cancellation_and_failure_isolation() -> None:
    calls: list[str] = []

    async def broken(event: HookEvent) -> None:
        raise RuntimeError("boom")

    async def cancel(event: HookEvent) -> HookDecision:
        calls.append("cancel")
        return HookDecision.CANCEL

    registry = HookRegistry()
    registry.register("event", broken, owner="broken", priority=20)
    registry.register("event", cancel, owner="cancel", priority=10)
    registry.register("event", lambda event: calls.append("later"), owner="later")
    report = asyncio.run(registry.dispatch_async(HookEvent("event", {})))
    assert report.failures == 1
    assert report.cancelled is True
    assert calls == ["cancel"]
