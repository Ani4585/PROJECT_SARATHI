"""Typed configuration field declarations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .errors import InvalidConfigurationError, MissingConfigurationError
from .keys import normalize_key


class _Missing:
    """Sentinel representing a field without a default value."""


MISSING = _Missing()


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ValueError("expected a boolean value")


@dataclass(frozen=True, slots=True)
class ConfigurationField:
    """Declare the conversion and validation rules for one setting."""

    key: str
    value_type: Callable[[Any], Any] = str
    required: bool = False
    default: object = MISSING
    validator: Callable[[Any], bool] | None = None
    secret: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", normalize_key(self.key))
        if self.required and self.default is not MISSING:
            raise ValueError("A required configuration field cannot have a default.")
        if not callable(self.value_type):
            raise TypeError("Configuration field value_type must be callable.")

    def resolve(self, values: dict[str, object]) -> object:
        """Resolve, convert, and validate this field from raw values."""

        if self.key not in values:
            if self.default is not MISSING:
                value = self.default
            elif self.required:
                raise MissingConfigurationError(self.key)
            else:
                return None
        else:
            value = values[self.key]

        try:
            converted = _parse_bool(value) if self.value_type is bool else self.value_type(value)
        except (TypeError, ValueError) as error:
            raise InvalidConfigurationError(self.key, value, str(error)) from error

        if self.validator is not None:
            try:
                valid = self.validator(converted)
            except Exception as error:
                raise InvalidConfigurationError(
                    self.key,
                    value,
                    f"validator raised {type(error).__name__}: {error}",
                ) from error
            if not valid:
                raise InvalidConfigurationError(self.key, value, "validation failed")

        return converted
