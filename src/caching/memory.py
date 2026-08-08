"""Thread-safe in-memory cache backend with TTL and bounded eviction."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from threading import RLock
from time import monotonic, perf_counter
from typing import Generic, TypeVar

from src.metrics import NoOpMetricsRegistry
from src.observability.contracts import MetricRecorder

from .errors import CacheKeyError
from .model import CacheLookup, CachePolicy, CacheStats, EvictionPolicy


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


@dataclass(slots=True)
class _Entry(Generic[V]):
    value: V
    expires_at: float | None


class InMemoryCache(Generic[K, V]):
    """Store values in process with deterministic expiration and eviction."""

    def __init__(
        self,
        policy: CachePolicy | None = None,
        *,
        name: str = "default",
        metrics: MetricRecorder | None = None,
        clock: Callable[[], float] = monotonic,
        timer: Callable[[], float] = perf_counter,
    ) -> None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Cache name must not be blank.")
        self._policy = policy or CachePolicy()
        self._name = normalized_name
        self._metrics = metrics or NoOpMetricsRegistry()
        self._clock = clock
        self._timer = timer
        self._entries: OrderedDict[K, _Entry[V]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._writes = 0
        self._deletes = 0
        self._evictions = 0
        self._expirations = 0
        self._lock = RLock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def policy(self) -> CachePolicy:
        return self._policy

    def get(self, key: K) -> CacheLookup[V]:
        self._validate_key(key)
        started = self._timer()
        try:
            with self._lock:
                entry = self._entries.get(key)
                if entry is None:
                    self._misses += 1
                    self._increment("cache.misses")
                    return CacheLookup(False)
                if self._expired(entry):
                    del self._entries[key]
                    self._expirations += 1
                    self._misses += 1
                    self._increment("cache.expirations")
                    self._increment("cache.misses")
                    self._size_metric()
                    return CacheLookup(False)
                if self._policy.eviction is EvictionPolicy.LRU:
                    self._entries.move_to_end(key)
                self._hits += 1
                self._increment("cache.hits")
                return CacheLookup(True, entry.value)
        finally:
            self._latency("get", started)

    def set(self, key: K, value: V, *, ttl_seconds: float | None = None) -> None:
        self._validate_key(key)
        ttl = self._policy.ttl_seconds if ttl_seconds is None else ttl_seconds
        if ttl is not None and ttl <= 0:
            raise ValueError("Cache TTL must be positive when provided.")
        started = self._timer()
        try:
            with self._lock:
                self._purge_expired()
                exists = key in self._entries
                maximum = self._policy.max_entries
                while not exists and maximum is not None and len(self._entries) >= maximum:
                    self._entries.popitem(last=False)
                    self._evictions += 1
                    self._increment("cache.evictions")
                expires_at = None if ttl is None else self._clock() + ttl
                self._entries[key] = _Entry(value, expires_at)
                if self._policy.eviction is EvictionPolicy.LRU:
                    self._entries.move_to_end(key)
                self._writes += 1
                self._increment("cache.writes")
                self._size_metric()
        finally:
            self._latency("set", started)

    def delete(self, key: K) -> bool:
        self._validate_key(key)
        started = self._timer()
        try:
            with self._lock:
                entry = self._entries.get(key)
                if entry is None:
                    return False
                if self._expired(entry):
                    del self._entries[key]
                    self._expirations += 1
                    self._increment("cache.expirations")
                    self._size_metric()
                    return False
                del self._entries[key]
                self._deletes += 1
                self._increment("cache.deletes")
                self._size_metric()
                return True
        finally:
            self._latency("delete", started)

    def clear(self) -> int:
        started = self._timer()
        try:
            with self._lock:
                self._purge_expired()
                removed = len(self._entries)
                self._entries.clear()
                self._deletes += removed
                if removed:
                    self._increment("cache.deletes", removed)
                self._size_metric()
                return removed
        finally:
            self._latency("clear", started)

    def keys(self) -> tuple[K, ...]:
        with self._lock:
            self._purge_expired()
            return tuple(self._entries)

    def stats(self) -> CacheStats:
        with self._lock:
            self._purge_expired()
            return CacheStats(
                len(self._entries),
                self._hits,
                self._misses,
                self._writes,
                self._deletes,
                self._evictions,
                self._expirations,
            )

    def _validate_key(self, key: K) -> None:
        try:
            hash(key)
        except TypeError as error:
            raise CacheKeyError("Cache keys must be hashable.") from error

    def _expired(self, entry: _Entry[V]) -> bool:
        return entry.expires_at is not None and self._clock() >= entry.expires_at

    def _purge_expired(self) -> None:
        expired = tuple(
            key for key, entry in self._entries.items() if self._expired(entry)
        )
        for key in expired:
            del self._entries[key]
        if expired:
            self._expirations += len(expired)
            self._increment("cache.expirations", len(expired))
            self._size_metric()

    def _labels(self, **extra: object) -> dict[str, object]:
        return {"cache": self._name, **extra}

    def _increment(self, name: str, amount: float = 1.0) -> None:
        self._metrics.increment(name, amount, self._labels())

    def _size_metric(self) -> None:
        self._metrics.set_gauge("cache.entries", len(self._entries), self._labels())

    def _latency(self, operation: str, started: float) -> None:
        self._metrics.observe(
            "cache.operation.duration",
            max(0.0, self._timer() - started),
            self._labels(operation=operation),
        )
