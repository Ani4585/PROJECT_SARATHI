"""Wall-time, CPU, and allocation profiling with enforceable budgets."""

from __future__ import annotations

import tracemalloc
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter, process_time

from src.observability import DiagnosticEvent, EventSink

from .model import PerformanceBudget, PerformanceSnapshot, PerformanceStatus


@dataclass(slots=True)
class ProfileSession:
    """Expose the completed immutable snapshot after a profiled block exits."""

    name: str
    snapshot: PerformanceSnapshot | None = None


class PerformanceProfiler:
    """Create performance sessions with an inexpensive disabled path."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        event_sink: EventSink | None = None,
        clock: Callable[[], float] = perf_counter,
        cpu_clock: Callable[[], float] = process_time,
        memory_start: Callable[[], None] = tracemalloc.start,
        memory_stop: Callable[[], None] = tracemalloc.stop,
        memory_sample: Callable[[], tuple[int, int]] = tracemalloc.get_traced_memory,
        memory_active: Callable[[], bool] = tracemalloc.is_tracing,
    ) -> None:
        self.enabled = enabled
        self._event_sink = event_sink
        self._clock = clock
        self._cpu_clock = cpu_clock
        self._memory_start = memory_start
        self._memory_stop = memory_stop
        self._memory_sample = memory_sample
        self._memory_active = memory_active

    @contextmanager
    def profile(
        self,
        name: str,
        budget: PerformanceBudget | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> Iterator[ProfileSession]:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Profile session name must not be blank.")
        session = ProfileSession(normalized)
        if not self.enabled:
            session.snapshot = PerformanceSnapshot(
                normalized, PerformanceStatus.DISABLED, 0.0, 0.0, 0, 0
            )
            yield session
            return

        started_memory = not self._memory_active()
        if started_memory:
            self._memory_start()
        base_current, _ = self._memory_sample()
        started = self._clock()
        cpu_started = self._cpu_clock()
        error_text: str | None = None
        try:
            yield session
        except Exception as error:
            error_text = f"{type(error).__name__}: {error}"
            raise
        finally:
            duration = max(0.0, self._clock() - started)
            cpu_duration = max(0.0, self._cpu_clock() - cpu_started)
            current, peak = self._memory_sample()
            current_delta = max(0, current - base_current)
            peak_delta = max(0, peak - base_current)
            if started_memory:
                self._memory_stop()
            violations = self._violations(budget, duration, cpu_duration, peak_delta)
            status = (
                PerformanceStatus.ERROR
                if error_text
                else PerformanceStatus.BUDGET_EXCEEDED
                if violations
                else PerformanceStatus.PASS
            )
            session.snapshot = PerformanceSnapshot(
                normalized,
                status,
                duration,
                cpu_duration,
                current_delta,
                peak_delta,
                violations,
                error_text,
            )
            self._publish(session.snapshot, attributes)

    @staticmethod
    def _violations(
        budget: PerformanceBudget | None,
        duration: float,
        cpu: float,
        peak_memory: int,
    ) -> tuple[str, ...]:
        if budget is None:
            return ()
        violations: list[str] = []
        if budget.max_duration_seconds is not None and duration > budget.max_duration_seconds:
            violations.append("duration")
        if budget.max_cpu_seconds is not None and cpu > budget.max_cpu_seconds:
            violations.append("cpu")
        if budget.max_peak_memory_bytes is not None and peak_memory > budget.max_peak_memory_bytes:
            violations.append("peak_memory")
        return tuple(violations)

    def _publish(self, snapshot: PerformanceSnapshot, attributes: Mapping[str, object] | None) -> None:
        if self._event_sink is None:
            return
        event_attributes = dict(attributes or {})
        event_attributes.update(
            {
                "profile": snapshot.name,
                "status": snapshot.status.value,
                "duration_seconds": snapshot.duration_seconds,
                "cpu_seconds": snapshot.cpu_seconds,
                "peak_memory_bytes": snapshot.peak_memory_bytes,
            }
        )
        try:
            self._event_sink.publish(DiagnosticEvent.create("performance.profile.completed", event_attributes))
        except Exception:
            pass
