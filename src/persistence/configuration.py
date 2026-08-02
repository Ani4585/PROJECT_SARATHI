"""Persistence configuration mapping."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .exceptions import PersistenceConfigurationError


@dataclass(frozen=True, slots=True)
class PersistenceSettings:
    adapter: str = "memory"
    database_name: str = "sarathi"

    def __post_init__(self) -> None:
        adapter = self.adapter.strip().casefold()
        database_name = self.database_name.strip()
        if adapter != "memory":
            raise PersistenceConfigurationError(
                f"Unsupported persistence adapter: {self.adapter}"
            )
        if not database_name:
            raise PersistenceConfigurationError("Persistence database name must not be blank.")
        object.__setattr__(self, "adapter", adapter)
        object.__setattr__(self, "database_name", database_name)

    @classmethod
    def from_configuration(
        cls,
        configuration: Mapping[str, object] | object,
        *,
        prefix: str = "persistence",
    ) -> "PersistenceSettings":
        section_method = getattr(configuration, "section", None)
        if callable(section_method):
            values = section_method(prefix)
        elif isinstance(configuration, Mapping):
            normalized_prefix = prefix.strip().casefold() + "."
            values = {
                str(key).casefold().removeprefix(normalized_prefix): value
                for key, value in configuration.items()
                if str(key).casefold().startswith(normalized_prefix)
            }
            values.update(
                {
                    str(key).casefold(): value
                    for key, value in configuration.items()
                    if str(key).casefold() in {"adapter", "database_name"}
                }
            )
        else:
            raise TypeError("Persistence configuration must be a mapping or Configuration.")
        adapter = values.get("adapter", "memory")
        database_name = values.get("database_name", "sarathi")
        if not isinstance(adapter, str) or not isinstance(database_name, str):
            raise PersistenceConfigurationError(
                "Persistence adapter and database name must be strings."
            )
        return cls(adapter, database_name)
