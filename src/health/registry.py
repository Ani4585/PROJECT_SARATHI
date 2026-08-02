"""Deterministic operational health-check registry."""

from __future__ import annotations

from .check import HealthCheck
from .model import HealthGroup


class HealthCheckRegistry:
    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck) -> None:
        if not isinstance(check, HealthCheck):
            raise TypeError("Health checks must implement HealthCheck.")
        name = check.name.strip()
        if not name or name != check.name:
            raise ValueError("Health check names must be nonblank without surrounding whitespace.")
        if name in self._checks:
            raise ValueError(f"Health check already registered: {name}")
        if check.timeout_seconds <= 0:
            raise ValueError("Health check timeout must be positive.")
        self._checks[name] = check

    def get(self, name: str) -> HealthCheck:
        return self._checks[name]

    def checks(self, groups: tuple[HealthGroup, ...] | None = None) -> tuple[HealthCheck, ...]:
        selected = set(groups or tuple(HealthGroup))
        return tuple(self._checks[name] for name in sorted(self._checks) if self._checks[name].group in selected)

    def __len__(self) -> int:
        return len(self._checks)
