"""Plugin manifests, lifecycle states, contexts, and operation results."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from collections.abc import Mapping


_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def version_tuple(value: str) -> tuple[int, int, int]:
    if not _VERSION.fullmatch(value):
        raise ValueError(f"Invalid semantic version: {value}")
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class PluginManifest:
    name: str
    version: str
    description: str
    minimum_framework_version: str = "0.0.0"
    maximum_framework_version: str | None = None
    required_capabilities: frozenset[str] = frozenset()
    provided_capabilities: frozenset[str] = frozenset()
    enabled_by_default: bool = True

    def __post_init__(self) -> None:
        name = self.name.strip()
        description = self.description.strip()
        if not name or not description:
            raise ValueError("Plugin name and description must not be blank.")
        if any(character.isspace() for character in name):
            raise ValueError("Plugin names must not contain whitespace.")
        version_tuple(self.version)
        version_tuple(self.minimum_framework_version)
        if self.maximum_framework_version is not None:
            version_tuple(self.maximum_framework_version)
            if version_tuple(self.maximum_framework_version) < version_tuple(self.minimum_framework_version):
                raise ValueError("Maximum framework version must not precede the minimum.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "required_capabilities", frozenset(item.strip() for item in self.required_capabilities if item.strip()))
        object.__setattr__(self, "provided_capabilities", frozenset(item.strip() for item in self.provided_capabilities if item.strip()))


class PluginState(StrEnum):
    REGISTERED = "registered"
    DISABLED = "disabled"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PluginContext:
    framework_version: str
    configuration: Mapping[str, object]
    capabilities: frozenset[str]

    def __post_init__(self) -> None:
        version_tuple(self.framework_version)
        object.__setattr__(self, "configuration", MappingProxyType(dict(self.configuration)))
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))


@dataclass(frozen=True, slots=True)
class PluginOperation:
    name: str
    state: PluginState
    message: str


@dataclass(frozen=True, slots=True)
class PluginReport:
    operations: tuple[PluginOperation, ...]

    @property
    def failures(self) -> int:
        return sum(item.state is PluginState.FAILED for item in self.operations)

    @property
    def passed(self) -> bool:
        return self.failures == 0

    def find(self, name: str) -> PluginOperation | None:
        return next((item for item in self.operations if item.name == name), None)
