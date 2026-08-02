"""Typed managed-resource models."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class ResourceState(StrEnum):
    REGISTERED = "registered"
    ACQUIRING = "acquiring"
    READY = "ready"
    RELEASING = "releasing"
    RELEASED = "released"
    FAILED = "failed"


class ResourceRegistryState(StrEnum):
    NEW = "new"
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ResourceDefinition:
    name: str
    factory: Callable[[], object]
    releaser: Callable[[object], None] | None = None
    dependencies: tuple[str, ...] = ()
    lazy: bool = False

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Resource name must not be blank.")
        if not callable(self.factory):
            raise TypeError("Resource factory must be callable.")
        if self.releaser is not None and not callable(self.releaser):
            raise TypeError("Resource releaser must be callable.")
        if any(not isinstance(item, str) for item in self.dependencies):
            raise TypeError("Resource dependencies must be strings.")
        dependencies = tuple(item.strip() for item in self.dependencies)
        if any(not item for item in dependencies):
            raise ValueError("Resource dependencies must not be blank.")
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("Resource dependencies must be unique.")
        if name in dependencies:
            raise ValueError("A resource cannot depend on itself.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "lazy", bool(self.lazy))


@dataclass(frozen=True, slots=True)
class ResourceCleanupFailure:
    resource: str
    message: str


@dataclass(frozen=True, slots=True)
class ResourceCloseReport:
    released: tuple[str, ...]
    failures: tuple[ResourceCleanupFailure, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass(frozen=True, slots=True)
class ResourceRegistrySnapshot:
    state: ResourceRegistryState
    resources: tuple[tuple[str, ResourceState, bool], ...]
    acquisition_order: tuple[str, ...]

    @property
    def ready(self) -> int:
        return sum(state is ResourceState.READY for _, state, _ in self.resources)

    @property
    def failed(self) -> int:
        return sum(state is ResourceState.FAILED for _, state, _ in self.resources)

    @property
    def pending_lazy(self) -> int:
        return sum(
            lazy and state is ResourceState.REGISTERED
            for _, state, lazy in self.resources
        )
