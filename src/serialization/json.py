"""Deterministic JSON serializer."""

from __future__ import annotations

import json

from .errors import SerializationDecodeError, SerializationEncodeError


class JsonSerializer:
    name = "json"
    media_type = "application/json"

    def __init__(self, *, indent: int | None = None, sort_keys: bool = True) -> None:
        self._indent = indent
        self._sort_keys = bool(sort_keys)

    def dumps(self, value: object) -> str:
        try:
            return json.dumps(
                value,
                indent=self._indent,
                sort_keys=self._sort_keys,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":") if self._indent is None else None,
            )
        except (TypeError, ValueError) as error:
            raise SerializationEncodeError(
                f"JSON encoding failed: {error}",
                details={"format": self.name, "reason": str(error)},
            ) from error

    def loads(self, document: str) -> object:
        if not isinstance(document, str):
            raise TypeError("Serialized documents must be strings.")
        try:
            return json.loads(document)
        except (json.JSONDecodeError, RecursionError) as error:
            raise SerializationDecodeError(
                f"JSON decoding failed: {error}",
                details={"format": self.name, "reason": str(error)},
            ) from error
