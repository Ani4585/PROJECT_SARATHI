"""Application-lifecycle adapter for the resource registry."""

from __future__ import annotations

from .model import ResourceCloseReport, ResourceRegistryState
from .registry import ResourceRegistry


class ResourceLifecycle:
    """Expose resource acquisition and cleanup as startup/shutdown operations."""

    def __init__(self, registry: ResourceRegistry) -> None:
        self._registry = registry

    @property
    def running(self) -> bool:
        return self._registry.state is ResourceRegistryState.OPEN

    def start(self) -> None:
        self._registry.open()

    def stop(self) -> ResourceCloseReport:
        return self._registry.close()
