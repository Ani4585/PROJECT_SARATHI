"""Cache policy, lookup, and statistics models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar


T = TypeVar("T")


class EvictionPolicy(StrEnum):
    LRU = "lru"
    FIFO = "fifo"


@dataclass(frozen=True, slots=True)
class CachePolicy:
    ttl_seconds: float | None = None
    max_entries: int | None = 1024
    eviction: EvictionPolicy = EvictionPolicy.LRU

    def __post_init__(self) -> None:
        if self.ttl_seconds is not None and self.ttl_seconds <= 0:
            raise ValueError("Cache TTL must be positive when provided.")
        if self.max_entries is not None:
            if (
                not isinstance(self.max_entries, int)
                or isinstance(self.max_entries, bool)
                or self.max_entries <= 0
            ):
                raise ValueError("Cache maximum entries must be a positive integer.")
        if not isinstance(self.eviction, EvictionPolicy):
            raise TypeError("Cache eviction policy must be an EvictionPolicy.")


@dataclass(frozen=True, slots=True)
class CacheLookup(Generic[T]):
    found: bool
    value: T | None = None


@dataclass(frozen=True, slots=True)
class CacheStats:
    entries: int
    hits: int
    misses: int
    writes: int
    deletes: int
    evictions: int
    expirations: int

    @property
    def requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / self.requests if self.requests else 0.0
