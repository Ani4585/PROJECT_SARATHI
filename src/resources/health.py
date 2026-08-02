"""Operational health integration for managed resources."""

from __future__ import annotations

from src.health import HealthCheck, HealthGroup, HealthResult, HealthStatus

from .model import ResourceRegistryState
from .registry import ResourceRegistry


class ResourceRegistryHealthCheck(HealthCheck):
    def __init__(
        self,
        registry: ResourceRegistry,
        *,
        group: HealthGroup = HealthGroup.READINESS,
        critical: bool = True,
    ) -> None:
        self._registry = registry
        self._group = group
        self._critical = bool(critical)

    @property
    def name(self) -> str:
        return f"{self.group.value}-resources"

    @property
    def group(self) -> HealthGroup:
        return self._group

    @property
    def critical(self) -> bool:
        return self._critical

    def run(self) -> HealthResult:
        snapshot = self._registry.snapshot()
        healthy = (
            snapshot.state is ResourceRegistryState.OPEN
            and snapshot.failed == 0
        )
        return HealthResult(
            self.name,
            self.group,
            HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
            (
                "Managed resources are available."
                if healthy
                else "Managed resources are not available."
            ),
            critical=self.critical,
            details=(
                f"Registry state: {snapshot.state.value}",
                f"Ready: {snapshot.ready}",
                f"Pending lazy: {snapshot.pending_lazy}",
                f"Failed: {snapshot.failed}",
            ),
        )
