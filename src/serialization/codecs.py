"""Typed object codecs and recursive document transformation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import Generic, TypeVar

from .contracts import Serializer
from .errors import SerializationDecodeError, SerializationEncodeError, SerializationTypeError


T = TypeVar("T")
TYPE_KEY = "$sarathi.type"
VALUE_KEY = "$sarathi.value"


@dataclass(frozen=True, slots=True)
class ObjectCodec(Generic[T]):
    type_name: str
    target_type: type[T]
    encoder: Callable[[T], object]
    decoder: Callable[[object], T]

    def __post_init__(self) -> None:
        type_name = self.type_name.strip()
        if not type_name:
            raise ValueError("Object codec type name must not be blank.")
        if not isinstance(self.target_type, type):
            raise TypeError("Object codec target must be a type.")
        if not callable(self.encoder) or not callable(self.decoder):
            raise TypeError("Object codec encoder and decoder must be callable.")
        object.__setattr__(self, "type_name", type_name)


class TypeCodecRegistry:
    """Register custom types and transform nested object graphs safely."""

    def __init__(self) -> None:
        self._by_name: dict[str, ObjectCodec] = {}
        self._by_type: dict[type, ObjectCodec] = {}

    def register(self, codec: ObjectCodec) -> None:
        if codec.type_name in self._by_name:
            raise ValueError(f"Object codec name already registered: {codec.type_name}")
        if codec.target_type in self._by_type:
            raise ValueError(
                f"Object codec type already registered: {codec.target_type.__qualname__}"
            )
        self._by_name[codec.type_name] = codec
        self._by_type[codec.target_type] = codec

    def register_dataclass(self, target_type: type[T], *, type_name: str | None = None) -> None:
        if not is_dataclass(target_type):
            raise TypeError("register_dataclass requires a dataclass type.")

        def encode(value: T) -> object:
            return {field.name: getattr(value, field.name) for field in fields(value)}

        def decode(value: object) -> T:
            if not isinstance(value, Mapping):
                raise TypeError("Dataclass payload must be a mapping.")
            return target_type(**dict(value))

        name = type_name or f"{target_type.__module__}.{target_type.__qualname__}"
        self.register(ObjectCodec(name, target_type, encode, decode))

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_name))

    def encode(self, value: object) -> object:
        if getattr(value, "__sarathi_secret__", False) is True:
            raise SerializationTypeError("Secret values cannot be serialized.")
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        codec = self._codec_for_value(value)
        if codec is not None:
            try:
                payload = codec.encoder(value)
            except Exception as error:
                raise SerializationEncodeError(
                    f"Object codec {codec.type_name!r} failed: {error}"
                ) from error
            return {TYPE_KEY: codec.type_name, VALUE_KEY: self.encode(payload)}
        if isinstance(value, list):
            return [self.encode(item) for item in value]
        if isinstance(value, tuple):
            return {TYPE_KEY: "builtins.tuple", VALUE_KEY: [self.encode(item) for item in value]}
        if isinstance(value, Mapping):
            if not all(isinstance(key, str) for key in value):
                raise SerializationTypeError("Serialized mapping keys must be strings.")
            encoded = {key: self.encode(item) for key, item in value.items()}
            if TYPE_KEY in encoded or VALUE_KEY in encoded:
                return {TYPE_KEY: "builtins.mapping", VALUE_KEY: encoded}
            return encoded
        raise SerializationTypeError(
            f"No object codec is registered for {type(value).__module__}.{type(value).__qualname__}."
        )

    def decode(self, value: object) -> object:
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        if isinstance(value, list):
            return [self.decode(item) for item in value]
        if not isinstance(value, Mapping):
            raise SerializationTypeError(
                f"Unsupported decoded value type: {type(value).__name__}."
            )
        if TYPE_KEY not in value:
            return {str(key): self.decode(item) for key, item in value.items()}
        if set(value) != {TYPE_KEY, VALUE_KEY}:
            raise SerializationDecodeError("Typed object envelope contains unexpected fields.")
        type_name = value[TYPE_KEY]
        if not isinstance(type_name, str):
            raise SerializationDecodeError("Typed object name must be a string.")
        if type_name == "builtins.tuple":
            raw_payload = value[VALUE_KEY]
            if not isinstance(raw_payload, list):
                raise SerializationDecodeError("Tuple payload must be a list.")
            return tuple(self.decode(item) for item in raw_payload)
        if type_name == "builtins.mapping":
            raw_payload = value[VALUE_KEY]
            if not isinstance(raw_payload, Mapping):
                raise SerializationDecodeError("Mapping payload must be a mapping.")
            return {
                str(key): self.decode(item)
                for key, item in raw_payload.items()
            }
        payload = self.decode(value[VALUE_KEY])
        try:
            codec = self._by_name[type_name]
        except KeyError as error:
            raise SerializationTypeError(f"Object codec is not registered: {type_name}") from error
        try:
            return codec.decoder(payload)
        except Exception as error:
            raise SerializationDecodeError(
                f"Object codec {type_name!r} failed: {error}"
            ) from error

    def _codec_for_value(self, value: object) -> ObjectCodec | None:
        exact = self._by_type.get(type(value))
        if exact is not None:
            return exact
        return next(
            (codec for target, codec in self._by_type.items() if isinstance(value, target)),
            None,
        )


class TypedSerializer:
    """Wrap any document serializer with registered object-graph codecs."""

    def __init__(self, serializer: Serializer, codecs: TypeCodecRegistry) -> None:
        self._serializer = serializer
        self._codecs = codecs

    @property
    def name(self) -> str:
        return self._serializer.name

    @property
    def media_type(self) -> str:
        return self._serializer.media_type

    def dumps(self, value: object) -> str:
        return self._serializer.dumps(self._codecs.encode(value))

    def loads(self, document: str) -> object:
        return self._codecs.decode(self._serializer.loads(document))
