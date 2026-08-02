"""Tests for official M15 performance monitoring."""

from __future__ import annotations

import json

import pytest

from src.observability import DiagnosticEventPublisher
from src.performance import (
    PerformanceBudget,
    PerformanceComparison,
    PerformanceJsonRenderer,
    PerformanceProfiler,
    PerformanceSnapshot,
    PerformanceStatus,
    PerformanceTextRenderer,
)


def deterministic_profiler(*, event_sink=None, enabled: bool = True):
    wall = iter((10.0, 12.0))
    cpu = iter((3.0, 4.0))
    memory = iter(((100, 100), (160, 240)))
    lifecycle: list[str] = []
    profiler = PerformanceProfiler(
        enabled=enabled,
        event_sink=event_sink,
        clock=lambda: next(wall),
        cpu_clock=lambda: next(cpu),
        memory_active=lambda: False,
        memory_start=lambda: lifecycle.append("start"),
        memory_stop=lambda: lifecycle.append("stop"),
        memory_sample=lambda: next(memory),
    )
    return profiler, lifecycle


def test_budget_rejects_negative_limits() -> None:
    with pytest.raises(ValueError):
        PerformanceBudget(max_duration_seconds=-1)


def test_profiler_captures_wall_cpu_and_allocation_snapshot() -> None:
    profiler, lifecycle = deterministic_profiler()
    with profiler.profile("operation") as session:
        pass
    assert session.snapshot is not None
    assert session.snapshot.status is PerformanceStatus.PASS
    assert session.snapshot.duration_seconds == 2.0
    assert session.snapshot.cpu_seconds == 1.0
    assert session.snapshot.current_memory_bytes == 60
    assert session.snapshot.peak_memory_bytes == 140
    assert lifecycle == ["start", "stop"]


def test_profiler_enforces_all_budget_dimensions() -> None:
    profiler, _ = deterministic_profiler()
    budget = PerformanceBudget(
        max_duration_seconds=1.0,
        max_cpu_seconds=0.5,
        max_peak_memory_bytes=100,
    )
    with profiler.profile("operation", budget) as session:
        pass
    assert session.snapshot is not None
    assert session.snapshot.status is PerformanceStatus.BUDGET_EXCEEDED
    assert session.snapshot.violations == ("duration", "cpu", "peak_memory")


def test_profiler_records_error_and_reraises() -> None:
    profiler, _ = deterministic_profiler()
    with pytest.raises(RuntimeError):
        with profiler.profile("failure") as session:
            raise RuntimeError("boom")
    assert session.snapshot is not None
    assert session.snapshot.status is PerformanceStatus.ERROR
    assert session.snapshot.error == "RuntimeError: boom"


def test_profiler_publishes_structured_observability_event() -> None:
    events = []
    publisher = DiagnosticEventPublisher()
    publisher.subscribe(events.append)
    profiler, _ = deterministic_profiler(event_sink=publisher)
    with profiler.profile("operation", attributes={"component": "test"}):
        pass
    assert len(events) == 1
    assert events[0].name == "performance.profile.completed"
    assert ("component", "test") in events[0].attributes
    assert ("status", "pass") in events[0].attributes


def test_disabled_profiler_avoids_clocks_memory_and_events() -> None:
    calls: list[str] = []

    def touched():
        calls.append("called")
        raise AssertionError("disabled profiler touched instrumentation")

    profiler = PerformanceProfiler(
        enabled=False,
        clock=touched,
        cpu_clock=touched,
        memory_start=touched,
        memory_stop=touched,
        memory_sample=touched,
        memory_active=touched,
    )
    with profiler.profile("disabled") as session:
        pass
    assert session.snapshot is not None
    assert session.snapshot.status is PerformanceStatus.DISABLED
    assert calls == []


def test_profiler_does_not_stop_preexisting_memory_tracing() -> None:
    wall = iter((0.0, 1.0))
    cpu = iter((0.0, 0.5))
    memory = iter(((10, 20), (15, 30)))
    calls: list[str] = []
    profiler = PerformanceProfiler(
        clock=lambda: next(wall),
        cpu_clock=lambda: next(cpu),
        memory_active=lambda: True,
        memory_start=lambda: calls.append("start"),
        memory_stop=lambda: calls.append("stop"),
        memory_sample=lambda: next(memory),
    )
    with profiler.profile("operation"):
        pass
    assert calls == []


def snapshots():
    baseline = PerformanceSnapshot("operation", PerformanceStatus.PASS, 1.0, 0.5, 10, 100)
    current = PerformanceSnapshot("operation", PerformanceStatus.PASS, 1.5, 0.4, 20, 125)
    return baseline, current


def test_comparison_calculates_changes() -> None:
    comparison = PerformanceComparison(*snapshots())
    assert comparison.duration_change_percent == 50.0
    assert comparison.cpu_change_percent == pytest.approx(-20.0)
    assert comparison.memory_change_percent == 25.0


def test_performance_renderers_generate_reports() -> None:
    baseline, current = snapshots()
    comparison = PerformanceComparison(baseline, current)
    text = PerformanceTextRenderer()
    assert "Duration change: +50.00%" in text.render_comparison(comparison)
    assert "Status: PASS" in text.render_snapshot(current)
    document = json.loads(PerformanceJsonRenderer().render_comparison(comparison))
    assert document["change_percent"]["peak_memory"] == 25.0


def test_profile_name_must_not_be_blank() -> None:
    profiler, _ = deterministic_profiler()
    with pytest.raises(ValueError):
        with profiler.profile(" "):
            pass
