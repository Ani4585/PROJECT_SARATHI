"""Dependency-aware module registry."""

from __future__ import annotations

from .exceptions import (
    ModuleAlreadyRegisteredError,
    ModuleCycleError,
    ModuleDependencyError,
)
from .module import Module


class ModuleRegistry:
    """Store modules and produce a deterministic dependency plan."""

    def __init__(self) -> None:
        self._modules: dict[str, Module] = {}

    def register(self, module: Module) -> None:
        name = module.name.strip()
        if not name:
            raise ValueError("Module name must not be blank.")
        if name in self._modules:
            raise ModuleAlreadyRegisteredError(name)
        dependencies = tuple(module.dependencies)
        if name in dependencies:
            raise ModuleCycleError((name,))
        self._modules[name] = module

    def get(self, name: str) -> Module:
        try:
            return self._modules[name]
        except KeyError as error:
            raise KeyError(f"Module {name!r} is not registered.") from error

    def plan(self) -> tuple[Module, ...]:
        """Return a stable topological plan respecting registration order."""

        for name, module in self._modules.items():
            for dependency in module.dependencies:
                if dependency not in self._modules:
                    raise ModuleDependencyError(name, dependency)

        remaining = {
            name: set(module.dependencies) for name, module in self._modules.items()
        }
        planned: list[str] = []
        while remaining:
            ready = tuple(name for name in self._modules if name in remaining and not remaining[name])
            if not ready:
                raise ModuleCycleError(tuple(name for name in self._modules if name in remaining))
            for name in ready:
                planned.append(name)
                remaining.pop(name)
                for dependencies in remaining.values():
                    dependencies.discard(name)
        return tuple(self._modules[name] for name in planned)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._modules)
