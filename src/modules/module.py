"""Module contracts and no-op base implementation."""

from __future__ import annotations

from typing import Protocol

from .descriptor import ModuleDescriptor, ModuleReloadPolicy


class Module(Protocol):
    """Pluggable platform capability with an explicit lifecycle."""

    @property
    def name(self) -> str:
        """Return the unique module name."""

    @property
    def dependencies(self) -> tuple[str, ...]:
        """Return names of modules that must start first."""

    @property
    def descriptor(self) -> ModuleDescriptor:
        """Return validated module metadata."""

    def configure(self, container: object) -> None:
        """Register services before the runtime starts."""

    def start(self, context: object) -> None:
        """Start module-owned runtime resources."""

    def stop(self, context: object) -> None:
        """Stop module-owned resources."""


class BaseModule:
    """Convenient module base with no-op lifecycle hooks."""

    name = "module"
    version = "0.0.0"
    description = "Framework module"
    dependencies: tuple[str, ...] = ()
    reload_policy = ModuleReloadPolicy.NEVER

    @property
    def descriptor(self) -> ModuleDescriptor:
        return ModuleDescriptor(
            name=self.name,
            version=self.version,
            description=self.description,
            dependencies=tuple(self.dependencies),
            reload_policy=self.reload_policy,
        )

    def configure(self, container: object) -> None:
        del container

    def start(self, context: object) -> None:
        del context

    def stop(self, context: object) -> None:
        del context
