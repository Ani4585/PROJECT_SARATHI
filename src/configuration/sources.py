"""Built-in sources for layered configuration loading."""

from __future__ import annotations

import os
import json
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .keys import normalize_key


class ConfigurationProvider(Protocol):
    """Contract implemented by configuration value providers."""

    @property
    def name(self) -> str:
        """Return a human-readable source name."""

    @property
    def priority(self) -> int:
        """Return precedence; larger values override smaller values."""

    def load(self) -> Mapping[str, object]:
        """Load raw configuration values."""


@dataclass(frozen=True, slots=True)
class MappingSource:
    """Provide configuration values from an in-memory mapping."""

    name: str
    values: Mapping[str, object]
    priority: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Configuration source name must not be blank.")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise TypeError("Configuration provider priority must be an integer.")

    def load(self) -> Mapping[str, object]:
        return {normalize_key(key): value for key, value in self.values.items()}


class EnvironmentSource:
    """Load prefixed environment variables as normalized setting keys."""

    def __init__(
        self,
        prefix: str = "SARATHI_",
        environment: Mapping[str, str] | None = None,
        *,
        priority: int = 100,
    ) -> None:
        if not prefix:
            raise ValueError("Environment prefix must not be blank.")
        self._prefix = prefix
        self._environment = environment
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise TypeError("Configuration provider priority must be an integer.")
        self._priority = priority

    @property
    def name(self) -> str:
        return "environment"

    @property
    def priority(self) -> int:
        return self._priority

    def load(self) -> Mapping[str, object]:
        environment = os.environ if self._environment is None else self._environment
        values: dict[str, object] = {}
        for key in sorted(environment):
            if key.upper().startswith(self._prefix.upper()):
                setting_key = key[len(self._prefix) :]
                values[normalize_key(setting_key)] = environment[key]
        return values


def _flatten_mapping(
    values: Mapping[str, object],
    prefix: str = "",
) -> dict[str, object]:
    flattened: dict[str, object] = {}
    for key, value in values.items():
        if not isinstance(key, str):
            raise TypeError("Configuration file keys must be strings.")
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping):
            flattened.update(_flatten_mapping(value, full_key))
        else:
            flattened[normalize_key(full_key)] = value
    return flattened


class FileSource:
    """Load flattened configuration values from JSON or TOML files."""

    def __init__(
        self,
        path: Path,
        *,
        name: str | None = None,
        priority: int = 50,
        optional: bool = False,
    ) -> None:
        self.path = Path(path)
        self._name = (name or f"file:{self.path.name}").strip()
        if not self._name:
            raise ValueError("Configuration source name must not be blank.")
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise TypeError("Configuration provider priority must be an integer.")
        self._priority = priority
        self.optional = bool(optional)

    @property
    def name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    def load(self) -> Mapping[str, object]:
        if not self.path.exists():
            if self.optional:
                return {}
            raise FileNotFoundError(f"Configuration file not found: {self.path}")
        suffix = self.path.suffix.casefold()
        if suffix == ".json":
            document = json.loads(self.path.read_text(encoding="utf-8"))
        elif suffix == ".toml":
            with self.path.open("rb") as stream:
                document = tomllib.load(stream)
        else:
            raise ValueError("Configuration files must use .json or .toml.")
        if not isinstance(document, Mapping):
            raise TypeError("Configuration file root must be an object or table.")
        return _flatten_mapping(document)


ConfigurationSource = ConfigurationProvider
