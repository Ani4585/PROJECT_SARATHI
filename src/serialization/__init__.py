"""Public PROJECT SARATHI serialization framework API."""

from .codecs import ObjectCodec, TypeCodecRegistry, TypedSerializer
from .contracts import Serializer
from .errors import (
    AdapterUnavailableError,
    MigrationError,
    SerializationDecodeError,
    SerializationEncodeError,
    SerializationError,
    SerializationTypeError,
    SerializerNotFoundError,
)
from .json import JsonSerializer
from .migration import MigrationRegistry, MigrationStep, VersionedSerializer
from .registry import SerializerRegistry, create_serializer_registry
from .toml import TomlSerializer
from .yaml import YamlSerializer

__all__ = [
    "AdapterUnavailableError",
    "JsonSerializer",
    "MigrationError",
    "MigrationRegistry",
    "MigrationStep",
    "ObjectCodec",
    "SerializationDecodeError",
    "SerializationEncodeError",
    "SerializationError",
    "SerializationTypeError",
    "Serializer",
    "SerializerNotFoundError",
    "SerializerRegistry",
    "TomlSerializer",
    "TypeCodecRegistry",
    "TypedSerializer",
    "VersionedSerializer",
    "YamlSerializer",
    "create_serializer_registry",
]
