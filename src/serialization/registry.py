"""Serializer registration and format resolution."""

from __future__ import annotations

from .contracts import Serializer
from .errors import SerializerNotFoundError


class SerializerRegistry:
    def __init__(self) -> None:
        self._serializers: dict[str, Serializer] = {}
        self._media_types: dict[str, str] = {}

    def register(self, serializer: Serializer) -> None:
        if not isinstance(serializer, Serializer):
            raise TypeError("Registered serializer must implement the Serializer contract.")
        name = serializer.name.strip().casefold()
        media_type = serializer.media_type.strip().casefold()
        if not name or not media_type:
            raise ValueError("Serializer name and media type must not be blank.")
        if name in self._serializers:
            raise ValueError(f"Serializer already registered: {name}")
        if media_type in self._media_types:
            raise ValueError(f"Serializer media type already registered: {media_type}")
        self._serializers[name] = serializer
        self._media_types[media_type] = name

    def get(self, name: str) -> Serializer:
        normalized = name.strip().casefold()
        try:
            return self._serializers[normalized]
        except KeyError as error:
            raise SerializerNotFoundError(normalized) from error

    def for_media_type(self, media_type: str) -> Serializer:
        normalized = media_type.split(";", 1)[0].strip().casefold()
        try:
            return self.get(self._media_types[normalized])
        except KeyError as error:
            raise SerializerNotFoundError(normalized) from error

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._serializers))

    def dumps(self, name: str, value: object) -> str:
        return self.get(name).dumps(value)

    def loads(self, name: str, document: str) -> object:
        return self.get(name).loads(document)


def create_serializer_registry(
    *,
    include_yaml: bool = True,
    include_toml: bool = True,
) -> SerializerRegistry:
    """Create the standard registry without importing optional adapters eagerly."""

    from .json import JsonSerializer

    registry = SerializerRegistry()
    registry.register(JsonSerializer())
    if include_yaml:
        from .yaml import YamlSerializer

        registry.register(YamlSerializer())
    if include_toml:
        from .toml import TomlSerializer

        registry.register(TomlSerializer())
    return registry
