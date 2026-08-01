"""Dependency-ordered module lifecycle runtime."""

from __future__ import annotations

from enum import Enum

from .exceptions import ModuleStartupError
from .module import Module
from .registry import ModuleRegistry


class ModuleRuntimeState(Enum):
    NEW = "NEW"
    CONFIGURED = "CONFIGURED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class ModuleRuntime:
    """Configure, start, rollback, and stop registered modules safely."""

    def __init__(self, registry: ModuleRegistry | None = None) -> None:
        self._registry = registry or ModuleRegistry()
        self._plan: tuple[Module, ...] = ()
        self._started: list[Module] = []
        self._state = ModuleRuntimeState.NEW

    @property
    def registry(self) -> ModuleRegistry:
        return self._registry

    @property
    def state(self) -> ModuleRuntimeState:
        return self._state

    @property
    def plan(self) -> tuple[str, ...]:
        return tuple(module.name for module in self._plan)

    def configure(self, container: object) -> None:
        if self._state is not ModuleRuntimeState.NEW:
            raise RuntimeError("Module runtime can only be configured once.")
        self._plan = self._registry.plan()
        for module in self._plan:
            module.configure(container)
        self._state = ModuleRuntimeState.CONFIGURED

    def start(self, context: object) -> None:
        if self._state is not ModuleRuntimeState.CONFIGURED:
            raise RuntimeError("Module runtime must be configured before start.")
        for module in self._plan:
            try:
                module.start(context)
            except Exception as error:
                for started in reversed(self._started):
                    try:
                        started.stop(context)
                    except Exception:
                        pass
                self._started.clear()
                self._state = ModuleRuntimeState.FAILED
                raise ModuleStartupError(
                    module.name, f"{type(error).__name__}: {error}"
                ) from error
            self._started.append(module)
        self._state = ModuleRuntimeState.RUNNING

    def stop(self, context: object) -> None:
        if self._state not in {ModuleRuntimeState.RUNNING, ModuleRuntimeState.FAILED}:
            raise RuntimeError("Module runtime is not running.")
        errors: list[str] = []
        for module in reversed(self._started):
            try:
                module.stop(context)
            except Exception as error:
                errors.append(f"{module.name}: {type(error).__name__}: {error}")
        self._started.clear()
        self._state = ModuleRuntimeState.STOPPED
        if errors:
            raise RuntimeError("Module shutdown failures: " + "; ".join(errors))
