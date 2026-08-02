"""Stable serializer contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Serializer(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def media_type(self) -> str: ...

    def dumps(self, value: object) -> str: ...

    def loads(self, document: str) -> object: ...
