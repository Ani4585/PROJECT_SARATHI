"""Ordered, duplicate-preserving HTTP headers."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping


_TOKEN = re.compile(rb"^[!#$%&'*+\-.^_`|~0-9a-z]+$")
HeaderPair = tuple[bytes, bytes]
HeaderInput = Mapping[str, str] | Iterable[tuple[str | bytes, str | bytes]]


def _name(value: str | bytes) -> bytes:
    encoded = value.encode("ascii") if isinstance(value, str) else bytes(value)
    encoded = encoded.lower()
    if not encoded or _TOKEN.fullmatch(encoded) is None:
        raise ValueError("HTTP header names must contain valid ASCII token characters.")
    return encoded


def _value(value: str | bytes) -> bytes:
    encoded = value.encode("latin-1") if isinstance(value, str) else bytes(value)
    if b"\r" in encoded or b"\n" in encoded:
        raise ValueError("HTTP header values must not contain line breaks.")
    return encoded


class Headers:
    """Immutable header collection preserving order and repeated fields."""

    def __init__(self, values: HeaderInput = ()) -> None:
        items = values.items() if isinstance(values, Mapping) else values
        self._raw = tuple((_name(name), _value(value)) for name, value in items)

    @property
    def raw(self) -> tuple[HeaderPair, ...]:
        return self._raw

    def get(self, name: str | bytes, default: str | None = None) -> str | None:
        target = _name(name)
        for header_name, value in self._raw:
            if header_name == target:
                return value.decode("latin-1")
        return default

    def get_all(self, name: str | bytes) -> tuple[str, ...]:
        target = _name(name)
        return tuple(
            value.decode("latin-1")
            for header_name, value in self._raw
            if header_name == target
        )

    def contains(self, name: str | bytes) -> bool:
        target = _name(name)
        return any(header_name == target for header_name, _ in self._raw)

    def appended(self, name: str | bytes, value: str | bytes) -> "Headers":
        return Headers((*self._raw, (_name(name), _value(value))))

    def with_default(self, name: str | bytes, value: str | bytes) -> "Headers":
        return self if self.contains(name) else self.appended(name, value)

    def replaced(self, name: str | bytes, value: str | bytes) -> "Headers":
        """Return headers with every existing occurrence replaced by one value."""

        target = _name(name)
        retained = tuple(pair for pair in self._raw if pair[0] != target)
        return Headers((*retained, (target, _value(value))))

    def __iter__(self) -> Iterator[HeaderPair]:
        return iter(self._raw)

    def __len__(self) -> int:
        return len(self._raw)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, (str, bytes)) and self.contains(name)
