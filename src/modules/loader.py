"""Validated module loading and development reload coordination."""

from __future__ import annotations

from dataclasses import dataclass

from .descriptor import ModuleDescriptor, ModuleReloadPolicy
from .exceptions import ModuleReloadError
from .module import Module
from .registry import ModuleRegistry
from .runtime import ModuleRuntime, ModuleRuntimeState


@dataclass(frozen=True, slots=True)
class ModuleLoadPlan:
    """Immutable dependency-ordered module loading plan."""

    descriptors: tuple[ModuleDescriptor, ...]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(descriptor.name for descriptor in self.descriptors)


class ModuleLoader:
    """Own module planning, lifecycle participation, and safe development reloads."""

    def __init__(
        self,
        registry: ModuleRegistry | None = None,
        *,
        development: bool = False,
    ) -> None:
        self._registry = registry or ModuleRegistry()
        self._runtime = ModuleRuntime(self._registry)
        self._development = bool(development)

    @property
    def registry(self) -> ModuleRegistry:
        return self._registry

    @property
    def state(self) -> ModuleRuntimeState:
        return self._runtime.state

    def add(self, module: Module) -> None:
        if self.state is not ModuleRuntimeState.NEW:
            raise RuntimeError("Modules can only be added before configuration.")
        self._registry.register(module)

    def plan(self) -> ModuleLoadPlan:
        modules = self._registry.plan()
        return ModuleLoadPlan(tuple(module.descriptor for module in modules))

    def configure(self, container: object) -> ModuleLoadPlan:
        plan = self.plan()
        self._runtime.configure(container)
        return plan

    def start(self, context: object) -> None:
        self._runtime.start(context)

    def stop(self, context: object) -> None:
        self._runtime.stop(context)

    def reload(self, name: str, replacement: Module) -> ModuleLoadPlan:
        """Replace a reloadable module while the lifecycle is inactive."""

        if not self._development:
            raise ModuleReloadError(name, "development mode is disabled")
        if self.state not in {ModuleRuntimeState.NEW, ModuleRuntimeState.STOPPED}:
            raise ModuleReloadError(name, f"runtime state is {self.state.value}")
        descriptor = self._registry.descriptor(name)
        if descriptor.reload_policy is not ModuleReloadPolicy.DEVELOPMENT:
            raise ModuleReloadError(name, "module reload policy is never")
        self._registry.replace(name, replacement)
        self._runtime = ModuleRuntime(self._registry)
        return self.plan()
