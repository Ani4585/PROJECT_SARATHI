"""Immutable resolved configuration values."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from types import MappingProxyType

from .errors import MissingConfigurationError
from .keys import normalize_key


class Configuration(Mapping[str, object]):
    """Expose immutable, normalized configuration values."""

    def __init__(
        self,
        values: Mapping[str, object],
        *,
        secret_keys: frozenset[str] = frozenset(),
    ) -> None:
        normalized = {normalize_key(key): value for key, value in values.items()}
        self._values = MappingProxyType(normalized)
        self._secret_keys = frozenset(normalize_key(key) for key in secret_keys)

    def __getitem__(self, key: str) -> object:
        return self._values[normalize_key(key)]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def require(self, key: str) -> object:
        """Return a value or raise a configuration-specific missing error."""

        normalized = normalize_key(key)
        if normalized not in self._values:
            raise MissingConfigurationError(normalized)
        return self._values[normalized]

    def section(self, prefix: str) -> dict[str, object]:
        """Return values below a dotted prefix with that prefix removed."""

        normalized = normalize_key(prefix) + "."
        return {
            key.removeprefix(normalized): value
            for key, value in self._values.items()
            if key.startswith(normalized)
        }

    def as_dict(self, *, redact_secrets: bool = True) -> dict[str, object]:
        """Return a detached dictionary, redacting declared secrets by default."""

        return {
            key: "********" if redact_secrets and key in self._secret_keys else value
            for key, value in self._values.items()
        }
