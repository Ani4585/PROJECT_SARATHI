"""Built-in secret providers."""

from __future__ import annotations

import json
import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.configuration.keys import normalize_key

from .errors import SecretProviderError


class SecretProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def priority(self) -> int: ...

    def load(self) -> Mapping[str, str]: ...


def _validate_priority(priority: int) -> int:
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise TypeError("Secret provider priority must be an integer.")
    return priority


def _normalize_values(values: Mapping[str, object]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in values.items():
        if not isinstance(key, str):
            raise SecretProviderError("Secret keys must be strings.")
        if not isinstance(value, str):
            raise SecretProviderError(
                f"Secret provider value for {normalize_key(key)!r} must be a string."
            )
        normalized[normalize_key(key)] = value
    return normalized


def _flatten(values: Mapping[str, object], prefix: str = "") -> dict[str, object]:
    flattened: dict[str, object] = {}
    for key, value in values.items():
        if not isinstance(key, str):
            raise SecretProviderError("Secret file keys must be strings.")
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping):
            flattened.update(_flatten(value, full_key))
        else:
            flattened[full_key] = value
    return flattened


@dataclass(frozen=True, slots=True)
class MappingSecretProvider:
    name: str
    values: Mapping[str, str]
    priority: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Secret provider name must not be blank.")
        _validate_priority(self.priority)

    def load(self) -> Mapping[str, str]:
        return _normalize_values(self.values)


class EnvironmentSecretProvider:
    def __init__(
        self,
        prefix: str = "SARATHI_SECRET_",
        environment: Mapping[str, str] | None = None,
        *,
        priority: int = 100,
    ) -> None:
        if not prefix:
            raise ValueError("Secret environment prefix must not be blank.")
        self._prefix = prefix
        self._environment = environment
        self._priority = _validate_priority(priority)

    @property
    def name(self) -> str:
        return "environment-secrets"

    @property
    def priority(self) -> int:
        return self._priority

    def load(self) -> Mapping[str, str]:
        environment = os.environ if self._environment is None else self._environment
        values = {
            key[len(self._prefix) :]: environment[key]
            for key in sorted(environment)
            if key.upper().startswith(self._prefix.upper())
        }
        return _normalize_values(values)


class FileSecretProvider:
    def __init__(
        self,
        path: Path,
        *,
        name: str | None = None,
        priority: int = 50,
        optional: bool = False,
    ) -> None:
        self.path = Path(path)
        self._name = (name or f"secret-file:{self.path.name}").strip()
        if not self._name:
            raise ValueError("Secret provider name must not be blank.")
        self._priority = _validate_priority(priority)
        self.optional = bool(optional)

    @property
    def name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    def load(self) -> Mapping[str, str]:
        if not self.path.exists():
            if self.optional:
                return {}
            raise FileNotFoundError(f"Secret file not found: {self.path}")
        try:
            suffix = self.path.suffix.casefold()
            if suffix == ".json":
                document = json.loads(self.path.read_text(encoding="utf-8"))
            elif suffix == ".toml":
                with self.path.open("rb") as stream:
                    document = tomllib.load(stream)
            else:
                raise SecretProviderError("Secret files must use .json or .toml.")
        except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
            raise SecretProviderError(
                f"Secret provider {self.name!r} could not load its file."
            ) from error
        if not isinstance(document, Mapping):
            raise SecretProviderError("Secret file root must be an object or table.")
        return _normalize_values(_flatten(document))
