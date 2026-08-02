"""Serialization framework exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class SerializationError(SarathiException):
    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message, error_code="SERIALIZATION_ERROR", details=details)


class SerializationEncodeError(SerializationError):
    pass


class SerializationDecodeError(SerializationError):
    pass


class SerializerNotFoundError(SerializationError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Serializer not registered: {name}", details={"name": name})


class SerializationTypeError(SerializationError):
    pass


class MigrationError(SerializationError):
    pass


class AdapterUnavailableError(SerializationError):
    pass
