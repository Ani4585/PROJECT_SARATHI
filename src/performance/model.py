"""Typed performance snapshots, budgets, and comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PerformanceStatus(StrEnum):
    PASS = "pass"
    BUDGET_EXCEEDED = "budget_exceeded"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class PerformanceBudget:
    max_duration_seconds: float | None = None
    max_cpu_seconds: float | None = None
    max_peak_memory_bytes: int | None = None

    def __post_init__(self) -> None:
        values = (self.max_duration_seconds, self.max_cpu_seconds, self.max_peak_memory_bytes)
        if any(value is not None and value < 0 for value in values):
            raise ValueError("Performance budgets must not be negative.")


@dataclass(frozen=True, slots=True)
class PerformanceSnapshot:
    name: str
    status: PerformanceStatus
    duration_seconds: float
    cpu_seconds: float
    current_memory_bytes: int
    peak_memory_bytes: int
    violations: tuple[str, ...] = ()
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.status in (PerformanceStatus.PASS, PerformanceStatus.DISABLED)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "cpu_seconds": self.cpu_seconds,
            "current_memory_bytes": self.current_memory_bytes,
            "peak_memory_bytes": self.peak_memory_bytes,
            "violations": list(self.violations),
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class PerformanceComparison:
    baseline: PerformanceSnapshot
    current: PerformanceSnapshot

    @staticmethod
    def _change(baseline: float, current: float) -> float | None:
        return None if baseline == 0 else ((current / baseline) - 1.0) * 100.0

    @property
    def duration_change_percent(self) -> float | None:
        return self._change(self.baseline.duration_seconds, self.current.duration_seconds)

    @property
    def cpu_change_percent(self) -> float | None:
        return self._change(self.baseline.cpu_seconds, self.current.cpu_seconds)

    @property
    def memory_change_percent(self) -> float | None:
        return self._change(float(self.baseline.peak_memory_bytes), float(self.current.peak_memory_bytes))

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline": self.baseline.to_dict(),
            "current": self.current.to_dict(),
            "change_percent": {
                "duration": self.duration_change_percent,
                "cpu": self.cpu_change_percent,
                "peak_memory": self.memory_change_percent,
            },
        }
