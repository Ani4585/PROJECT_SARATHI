"""Module contracts and no-op base implementation."""

from __future__ import annotations

from typing import Protocol


class Module(Protocol):
    """Pluggable platform capability with an explicit lifecycle."""

    @property
    def name(self) -> str:
        """Return the unique module name."""

    @property
    def dependencies(self) -> tuple[str, ...]:
        """Return names of modules that must start first."""

    def configure(self, container: object) -> None:
        """Register services before the runtime starts."""

    def start(self, context: object) -> None:
        """Start module-owned runtime resources."""

    def stop(self, context: object) -> None:
        """Stop module-owned resources."""


class BaseModule:
    """Convenient module base with no-op lifecycle hooks."""

    name = "module"
    dependencies: tuple[str, ...] = ()

    def configure(self, container: object) -> None:
        del container

    def start(self, context: object) -> None:
        del context

    def stop(self, context: object) -> None:
        del context
