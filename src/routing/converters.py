"""Typed path parameter converters."""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Protocol
from uuid import UUID

from .exceptions import ParameterConversionError, UnknownConverterError


class PathConverter(Protocol):
    regex: str
    weight: int

    def parse(self, value: str) -> object: ...

    def format(self, value: object) -> str: ...


class StringConverter:
    regex = r"[^/]+"
    weight = 20

    def parse(self, value: str) -> str:
        return value

    def format(self, value: object) -> str:
        text = str(value)
        if not text or "/" in text:
            raise ParameterConversionError("String path values must be non-empty segments.")
        return text


class IntegerConverter:
    regex = r"[0-9]+"
    weight = 30

    def parse(self, value: str) -> int:
        return int(value)

    def format(self, value: object) -> str:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ParameterConversionError(
                "Integer path values must be non-negative integers."
            )
        return str(value)


class UUIDConverter:
    regex = (
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
        r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
    )
    weight = 30

    def parse(self, value: str) -> UUID:
        return UUID(value)

    def format(self, value: object) -> str:
        try:
            return str(value if isinstance(value, UUID) else UUID(str(value)))
        except (AttributeError, TypeError, ValueError) as error:
            raise ParameterConversionError("UUID path value is invalid.") from error


class RemainderConverter:
    regex = r".+"
    weight = 10

    def parse(self, value: str) -> str:
        return value

    def format(self, value: object) -> str:
        text = str(value).strip("/")
        if not text:
            raise ParameterConversionError("Path remainder values must be non-empty.")
        return text


class ConverterRegistry:
    """Validated named converter collection."""

    def __init__(self, converters: Mapping[str, PathConverter] | None = None) -> None:
        self._converters: dict[str, PathConverter] = {}
        for name, converter in (converters or {}).items():
            self.register(name, converter)

    @classmethod
    def defaults(cls) -> "ConverterRegistry":
        return cls(
            {
                "str": StringConverter(),
                "int": IntegerConverter(),
                "uuid": UUIDConverter(),
                "path": RemainderConverter(),
            }
        )

    @property
    def converters(self) -> Mapping[str, PathConverter]:
        return MappingProxyType(dict(self._converters))

    def register(self, name: str, converter: PathConverter) -> None:
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError("Converter name must be a valid identifier.")
        if name in self._converters:
            raise ValueError(f"Converter {name!r} is already registered.")
        regex = getattr(converter, "regex", None)
        weight = getattr(converter, "weight", None)
        if (
            not isinstance(regex, str)
            or not regex
            or not isinstance(weight, int)
            or isinstance(weight, bool)
            or not callable(getattr(converter, "parse", None))
            or not callable(getattr(converter, "format", None))
        ):
            raise TypeError("Path converter does not satisfy the converter contract.")
        try:
            re.compile(regex)
        except re.error as error:
            raise ValueError("Path converter regex is invalid.") from error
        self._converters[name] = converter

    def get(self, name: str) -> PathConverter:
        try:
            return self._converters[name]
        except KeyError as error:
            raise UnknownConverterError(f"Unknown path converter: {name!r}.") from error
