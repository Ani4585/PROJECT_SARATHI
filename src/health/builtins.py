"""Built-in configuration, container, and filesystem health checks."""

from __future__ import annotations

from pathlib import Path

from src.container import ServiceContainer

from .check import HealthCheck
from .model import HealthGroup, HealthResult, HealthStatus


class FilesystemHealthCheck(HealthCheck):
    def __init__(self, project_root: Path, group: HealthGroup = HealthGroup.LIVENESS) -> None:
        self._root = project_root.resolve()
        self._group = group

    @property
    def name(self) -> str:
        return f"{self.group.value}-filesystem"

    @property
    def group(self) -> HealthGroup:
        return self._group

    def run(self) -> HealthResult:
        missing = tuple(name for name in ("src", "config", "docs") if not (self._root / name).is_dir())
        return HealthResult(
            self.name,
            self.group,
            HealthStatus.UNHEALTHY if missing else HealthStatus.HEALTHY,
            "Required framework directories are available." if not missing else "Required framework directories are missing.",
            details=(("Missing: " + ", ".join(missing)),) if missing else (f"Root: {self._root}",),
        )


class ConfigurationHealthCheck(HealthCheck):
    def __init__(self, project_root: Path, group: HealthGroup) -> None:
        self._root = project_root.resolve()
        self._group = group

    @property
    def name(self) -> str:
        return f"{self.group.value}-configuration"

    @property
    def group(self) -> HealthGroup:
        return self._group

    def run(self) -> HealthResult:
        settings = self._root / "config" / "settings.py"
        present = settings.is_file() and settings.stat().st_size > 0
        return HealthResult(
            self.name,
            self.group,
            HealthStatus.HEALTHY if present else HealthStatus.UNHEALTHY,
            "Configuration metadata is available." if present else "Configuration metadata is missing or empty.",
            details=(f"Path: {settings}",),
        )


class ContainerHealthCheck(HealthCheck):
    def __init__(self, group: HealthGroup) -> None:
        self._group = group

    @property
    def name(self) -> str:
        return f"{self.group.value}-container"

    @property
    def group(self) -> HealthGroup:
        return self._group

    @property
    def dependencies(self) -> tuple[str, ...]:
        return (f"{self.group.value}-configuration",)

    def run(self) -> HealthResult:
        container = ServiceContainer()
        return HealthResult(
            self.name,
            self.group,
            HealthStatus.HEALTHY,
            "Dependency injection container initialized successfully.",
            details=(f"Container: {type(container).__name__}",),
        )


def create_default_health_registry(project_root: Path):
    """Create the standard liveness, readiness, and startup registry."""

    from .registry import HealthCheckRegistry

    registry = HealthCheckRegistry()
    registry.register(FilesystemHealthCheck(project_root))
    for group in (HealthGroup.READINESS, HealthGroup.STARTUP):
        registry.register(ConfigurationHealthCheck(project_root, group))
        registry.register(ContainerHealthCheck(group))
    return registry
