"""Built-in sources for layered configuration loading."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from .keys import normalize_key


class ConfigurationSource(Protocol):
    """Contract implemented by configuration value providers."""

    @property
    def name(self) -> str:
        """Return a human-readable source name."""

    def load(self) -> Mapping[str, object]:
        """Load raw configuration values."""


@dataclass(frozen=True, slots=True)
class MappingSource:
    """Provide configuration values from an in-memory mapping."""

    name: str
    values: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Configuration source name must not be blank.")

    def load(self) -> Mapping[str, object]:
        return {normalize_key(key): value for key, value in self.values.items()}


class EnvironmentSource:
    """Load prefixed environment variables as normalized setting keys."""

    def __init__(
        self,
        prefix: str = "SARATHI_",
        environment: Mapping[str, str] | None = None,
    ) -> None:
        if not prefix:
            raise ValueError("Environment prefix must not be blank.")
        self._prefix = prefix
        self._environment = environment

    @property
    def name(self) -> str:
        return "environment"

    def load(self) -> Mapping[str, object]:
        environment = os.environ if self._environment is None else self._environment
        values: dict[str, object] = {}
        for key in sorted(environment):
            if key.upper().startswith(self._prefix.upper()):
                setting_key = key[len(self._prefix) :]
                values[normalize_key(setting_key)] = environment[key]
        return values
