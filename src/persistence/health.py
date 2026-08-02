"""Operational health integration for persistence."""

from __future__ import annotations

from src.health import HealthCheck, HealthGroup, HealthResult, HealthStatus

from .runtime import PersistenceRuntime


class PersistenceHealthCheck(HealthCheck):
    def __init__(
        self,
        runtime: PersistenceRuntime,
        *,
        group: HealthGroup = HealthGroup.READINESS,
        critical: bool = True,
    ) -> None:
        self._runtime = runtime
        self._group = group
        self._critical = bool(critical)

    @property
    def name(self) -> str:
        return f"{self.group.value}-persistence"

    @property
    def group(self) -> HealthGroup:
        return self._group

    @property
    def critical(self) -> bool:
        return self._critical

    def run(self) -> HealthResult:
        healthy = self._runtime.healthy
        return HealthResult(
            self.name,
            self.group,
            HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
            (
                "Persistence connection is available."
                if healthy
                else "Persistence connection is unavailable."
            ),
            critical=self.critical,
            details=(
                f"Adapter: {self._runtime.settings.adapter}",
                f"Database: {self._runtime.settings.database_name}",
            ),
        )
