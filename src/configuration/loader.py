"""Deterministic layered configuration loader."""

from __future__ import annotations

from collections.abc import Iterable

from .configuration import Configuration, ValueProvenance
from .errors import ConfigurationError, UnknownConfigurationError
from .keys import normalize_key
from .schema import ConfigurationField
from .sources import ConfigurationProvider


class ConfigurationLoader:
    """Merge ordered sources and resolve values against a typed schema."""

    def __init__(
        self,
        fields: Iterable[ConfigurationField],
        sources: Iterable[ConfigurationProvider],
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
        names = tuple(source.name for source in self._sources)
        if len(names) != len(set(names)):
            raise ValueError("Configuration provider names must be unique.")
        self._allow_unknown = allow_unknown

    @property
    def source_names(self) -> tuple[str, ...]:
        return tuple(source.name for source in self._ordered_sources())

    def _ordered_sources(self) -> tuple[ConfigurationProvider, ...]:
        """Return low-to-high precedence with declaration order breaking ties."""

        indexed = tuple(enumerate(self._sources))
        return tuple(
            source
            for index, source in sorted(
                indexed,
                key=lambda item: (getattr(item[1], "priority", 0), item[0]),
            )
        )

    def load(self) -> Configuration:
        """Load all sources in order; values from later sources win."""

        raw_values: dict[str, object] = {}
        provenance: dict[str, ValueProvenance] = {}
        for source in self._ordered_sources():
            try:
                loaded = source.load()
            except ConfigurationError:
                raise
            except Exception as error:
                raise ConfigurationError(
                    f"Configuration source {source.name!r} failed: {error}",
                    details={"source": source.name, "error": str(error)},
                ) from error
            priority = getattr(source, "priority", 0)
            normalized = {normalize_key(key): value for key, value in loaded.items()}
            raw_values.update(normalized)
            provenance.update(
                (key, ValueProvenance(source.name, priority)) for key in normalized
            )

        declared_keys = {field.key for field in self._fields}
        unknown = tuple(sorted(set(raw_values) - declared_keys))
        if unknown and not self._allow_unknown:
            raise UnknownConfigurationError(unknown)

        resolved = {field.key: field.resolve(raw_values) for field in self._fields}
        resolved_provenance = {
            field.key: provenance.get(
                field.key,
                ValueProvenance("schema-default", -1),
            )
            for field in self._fields
        }
        if self._allow_unknown:
            resolved.update(
                (key, value) for key, value in raw_values.items() if key not in declared_keys
            )
            resolved_provenance.update(
                (key, provenance[key]) for key in raw_values if key not in declared_keys
            )

        secrets = frozenset(field.key for field in self._fields if field.secret)
        return Configuration(
            resolved,
            secret_keys=secrets,
            provenance=resolved_provenance,
        )
