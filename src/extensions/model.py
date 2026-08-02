"""Typed extension points, registrations, policies, and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar


ExtensionValue = TypeVar("ExtensionValue")


class ExtensionPolicy(StrEnum):
    """How registrations at an extension point are resolved."""

    SINGLE = "single"
    COMPOSE = "compose"
    REPLACE = "replace"


@dataclass(frozen=True, slots=True)
class ExtensionPoint(Generic[ExtensionValue]):
    """A named extension contract and its resolution policy."""

    name: str
    contract: type[ExtensionValue]
    policy: ExtensionPolicy = ExtensionPolicy.COMPOSE
    description: str = ""

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name or any(character.isspace() for character in name):
            raise ValueError("Extension-point names must be non-empty and contain no whitespace.")
        if not isinstance(self.contract, type):
            raise TypeError("Extension-point contracts must be runtime-checkable types.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", self.description.strip())


@dataclass(frozen=True, slots=True)
class ExtensionRegistration(Generic[ExtensionValue]):
    """An extension value registered by an owning component."""

    point_name: str
    owner: str
    value: ExtensionValue
    priority: int = 0

    def __post_init__(self) -> None:
        owner = self.owner.strip()
        if not owner:
            raise ValueError("Extension owners must not be blank.")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise TypeError("Extension priority must be an integer.")
        object.__setattr__(self, "owner", owner)


@dataclass(frozen=True, slots=True)
class ExtensionPointDiagnostic:
    """Resolution details for one defined extension point."""

    name: str
    contract: str
    policy: ExtensionPolicy
    registrations: int
    active_owners: tuple[str, ...]
    shadowed_owners: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExtensionDiagnostics:
    """Immutable diagnostics for all extension points."""

    points: tuple[ExtensionPointDiagnostic, ...]

    @property
    def total_points(self) -> int:
        return len(self.points)

    @property
    def total_registrations(self) -> int:
        return sum(point.registrations for point in self.points)

    @property
    def shadowed_registrations(self) -> int:
        return sum(len(point.shadowed_owners) for point in self.points)
