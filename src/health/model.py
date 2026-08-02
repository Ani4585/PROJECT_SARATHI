"""Typed operational health models and aggregation rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HealthGroup(StrEnum):
    LIVENESS = "liveness"
    READINESS = "readiness"
    STARTUP = "startup"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class HealthResult:
    name: str
    group: HealthGroup
    status: HealthStatus
    summary: str
    duration_seconds: float = 0.0
    critical: bool = True
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        name = self.name.strip()
        summary = self.summary.strip()
        if not name or not summary:
            raise ValueError("Health result name and summary must not be blank.")
        if self.duration_seconds < 0:
            raise ValueError("Health result duration must not be negative.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "details", tuple(item.strip() for item in self.details if item.strip()))

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "group": self.group.value,
            "status": self.status.value,
            "summary": self.summary,
            "duration_seconds": self.duration_seconds,
            "critical": self.critical,
            "details": list(self.details),
        }


@dataclass(frozen=True, slots=True)
class HealthReport:
    groups: tuple[HealthGroup, ...]
    results: tuple[HealthResult, ...]
    duration_seconds: float

    @property
    def status(self) -> HealthStatus:
        if any(result.critical and result.status is HealthStatus.UNHEALTHY for result in self.results):
            return HealthStatus.UNHEALTHY
        if any(result.status in (HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.SKIPPED) for result in self.results):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    @property
    def passed(self) -> bool:
        return self.status is not HealthStatus.UNHEALTHY

    def to_dict(self) -> dict[str, object]:
        return {
            "title": "PROJECT SARATHI Health Report",
            "summary": {
                "status": self.status.value,
                "passed": self.passed,
                "groups": [group.value for group in self.groups],
                "checks": len(self.results),
                "duration_seconds": self.duration_seconds,
            },
            "results": [result.to_dict() for result in self.results],
        }
