"""Dependency-aware module registry."""

from __future__ import annotations

from .exceptions import (
    ModuleAlreadyRegisteredError,
    ModuleCycleError,
    ModuleDependencyError,
)
from .descriptor import ModuleDescriptor
from .module import Module


class ModuleRegistry:
    """Store modules and produce a deterministic dependency plan."""

    def __init__(self) -> None:
        self._modules: dict[str, Module] = {}
        self._descriptors: dict[str, ModuleDescriptor] = {}

    def register(self, module: Module) -> None:
        descriptor = module.descriptor
        if not isinstance(descriptor, ModuleDescriptor):
            raise TypeError("Module descriptor must be a ModuleDescriptor.")
        name = descriptor.name
        if module.name.strip() != name:
            raise ValueError("Module name must match its descriptor name.")
        if name in self._modules:
            raise ModuleAlreadyRegisteredError(name)
        if tuple(module.dependencies) != descriptor.dependencies:
            raise ValueError("Module dependencies must match its descriptor dependencies.")
        self._modules[name] = module
        self._descriptors[name] = descriptor

    def get(self, name: str) -> Module:
        try:
            return self._modules[name]
        except KeyError as error:
            raise KeyError(f"Module {name!r} is not registered.") from error

    def descriptor(self, name: str) -> ModuleDescriptor:
        try:
            return self._descriptors[name]
        except KeyError as error:
            raise KeyError(f"Module {name!r} is not registered.") from error

    def replace(self, name: str, module: Module) -> None:
        """Replace one module and retain the previous graph on validation failure."""

        if name not in self._modules:
            raise KeyError(f"Module {name!r} is not registered.")
        descriptor = module.descriptor
        if descriptor.name != name or module.name.strip() != name:
            raise ValueError("Replacement module must keep the registered module name.")
        if tuple(module.dependencies) != descriptor.dependencies:
            raise ValueError("Module dependencies must match its descriptor dependencies.")
        previous_module = self._modules[name]
        previous_descriptor = self._descriptors[name]
        self._modules[name] = module
        self._descriptors[name] = descriptor
        try:
            self.plan()
        except Exception:
            self._modules[name] = previous_module
            self._descriptors[name] = previous_descriptor
            raise

    def plan(self) -> tuple[Module, ...]:
        """Return a stable topological plan respecting registration order."""

        for name, descriptor in self._descriptors.items():
            for dependency in descriptor.dependencies:
                if dependency not in self._modules:
                    raise ModuleDependencyError(name, dependency)

        remaining = {
            name: set(descriptor.dependencies) for name, descriptor in self._descriptors.items()
        }
        planned: list[str] = []
        while remaining:
            ready = tuple(sorted(name for name, dependencies in remaining.items() if not dependencies))
            if not ready:
                raise ModuleCycleError(tuple(sorted(remaining)))
            for name in ready:
                planned.append(name)
                remaining.pop(name)
                for dependencies in remaining.values():
                    dependencies.discard(name)
        return tuple(self._modules[name] for name in planned)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._modules))
