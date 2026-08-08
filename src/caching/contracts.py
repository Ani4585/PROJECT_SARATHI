"""Stable cache backend contract."""

from __future__ import annotations

from collections.abc import Hashable
from typing import Protocol, TypeVar

from .model import CacheLookup, CacheStats


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class CacheBackend(Protocol[K, V]):
    def get(self, key: K) -> CacheLookup[V]: ...

    def set(self, key: K, value: V, *, ttl_seconds: float | None = None) -> None: ...

    def delete(self, key: K) -> bool: ...

    def clear(self) -> int: ...

    def keys(self) -> tuple[K, ...]: ...

    def stats(self) -> CacheStats: ...
