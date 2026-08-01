"""Deterministic layered configuration loader."""

from __future__ import annotations

from collections.abc import Iterable

from .configuration import Configuration
from .errors import ConfigurationError, UnknownConfigurationError
from .keys import normalize_key
from .schema import ConfigurationField
from .sources import ConfigurationSource


class ConfigurationLoader:
    """Merge ordered sources and resolve values against a typed schema."""

    def __init__(
        self,
        fields: Iterable[ConfigurationField],
        sources: Iterable[ConfigurationSource],
        *,
        allow_unknown: bool = False,
    ) -> None:
        self._fields = tuple(fields)
        self._sources = tuple(sources)
        keys = tuple(field.key for field in self._fields)
        if len(keys) != len(set(keys)):
            raise ValueError("Configuration schema contains duplicate keys.")
        if not self._sources:
            raise ValueError("At least one configuration source is required.")
        self._allow_unknown = allow_unknown

    @property
    def source_names(self) -> tuple[str, ...]:
        return tuple(source.name for source in self._sources)

    def load(self) -> Configuration:
        """Load all sources in order; values from later sources win."""

        raw_values: dict[str, object] = {}
        for source in self._sources:
            try:
                loaded = source.load()
            except ConfigurationError:
                raise
            except Exception as error:
                raise ConfigurationError(
                    f"Configuration source {source.name!r} failed: {error}",
                    details={"source": source.name, "error": str(error)},
                ) from error
            raw_values.update(
                {normalize_key(key): value for key, value in loaded.items()}
            )

        declared_keys = {field.key for field in self._fields}
        unknown = tuple(sorted(set(raw_values) - declared_keys))
        if unknown and not self._allow_unknown:
            raise UnknownConfigurationError(unknown)

        resolved = {field.key: field.resolve(raw_values) for field in self._fields}
        if self._allow_unknown:
            resolved.update(
                (key, value) for key, value in raw_values.items() if key not in declared_keys
            )

        secrets = frozenset(field.key for field in self._fields if field.secret)
        return Configuration(resolved, secret_keys=secrets)
