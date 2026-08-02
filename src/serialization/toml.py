"""TOML serializer adapter for nested tables and standard scalar values."""

from __future__ import annotations

import json
import math
import re
import tomllib
from collections.abc import Mapping
from datetime import date, datetime, time

from .errors import SerializationDecodeError, SerializationEncodeError


_BARE_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


def _key(value: str) -> str:
    return value if _BARE_KEY.fullmatch(value) else json.dumps(value, ensure_ascii=False)


def _value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("TOML does not support non-finite floats.")
        return repr(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_value(item) for item in value) + "]"
    raise TypeError(f"Unsupported TOML value type: {type(value).__name__}")


def _emit_table(
    document: Mapping[str, object],
    path: tuple[str, ...],
    lines: list[str],
) -> None:
    scalars: list[tuple[str, object]] = []
    tables: list[tuple[str, Mapping[str, object]]] = []
    for key in sorted(document):
        if not isinstance(key, str):
            raise TypeError("TOML keys must be strings.")
        value = document[key]
        if isinstance(value, Mapping):
            tables.append((key, value))
        else:
            scalars.append((key, value))
    if path:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append("[" + ".".join(_key(part) for part in path) + "]")
    for key, value in scalars:
        lines.append(f"{_key(key)} = {_value(value)}")
    for key, table in tables:
        _emit_table(table, (*path, key), lines)


class TomlSerializer:
    name = "toml"
    media_type = "application/toml"

    def dumps(self, value: object) -> str:
        if not isinstance(value, Mapping):
            raise SerializationEncodeError("TOML document root must be a mapping.")
        try:
            lines: list[str] = []
            _emit_table(value, (), lines)
            return "\n".join(lines).rstrip() + "\n"
        except (TypeError, ValueError) as error:
            raise SerializationEncodeError(
                f"TOML encoding failed: {error}",
                details={"format": self.name, "reason": str(error)},
            ) from error

    def loads(self, document: str) -> object:
        if not isinstance(document, str):
            raise TypeError("Serialized documents must be strings.")
        try:
            return tomllib.loads(document)
        except (tomllib.TOMLDecodeError, ValueError) as error:
            raise SerializationDecodeError(
                f"TOML decoding failed: {error}",
                details={"format": self.name, "reason": str(error)},
            ) from error
