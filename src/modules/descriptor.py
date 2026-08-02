"""Validated module descriptors and development reload policy."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


_SEMANTIC_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


class ModuleReloadPolicy(StrEnum):
    """Control whether a module may be replaced during development."""

    NEVER = "never"
    DEVELOPMENT = "development"


@dataclass(frozen=True, slots=True)
class ModuleDescriptor:
    """Stable metadata used to validate and plan a framework module."""

    name: str
    version: str
    description: str
    dependencies: tuple[str, ...] = ()
    reload_policy: ModuleReloadPolicy = ModuleReloadPolicy.NEVER

    def __post_init__(self) -> None:
        name = self.name.strip()
        description = self.description.strip()
        if not name or any(character.isspace() for character in name):
            raise ValueError("Module names must be non-empty and contain no whitespace.")
        if not _SEMANTIC_VERSION.fullmatch(self.version):
            raise ValueError(f"Invalid module semantic version: {self.version}")
        if not description:
            raise ValueError("Module description must not be blank.")
        dependencies = tuple(dependency.strip() for dependency in self.dependencies)
        if any(not dependency for dependency in dependencies):
            raise ValueError("Module dependencies must not be blank.")
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("Module dependencies must not contain duplicates.")
        if name in dependencies:
            raise ValueError("A module cannot depend on itself.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "dependencies", dependencies)
