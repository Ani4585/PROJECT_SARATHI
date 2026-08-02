"""Cache-aside loading with per-key stampede protection."""

from __future__ import annotations

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from threading import Lock, RLock, local
from time import perf_counter
from typing import Generic, TypeVar, cast

from src.metrics import NoOpMetricsRegistry
from src.observability.contracts import MetricRecorder

from .contracts import CacheBackend
from .errors import CacheLoadError


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


@dataclass(slots=True)
class _Flight:
    lock: Lock
    users: int = 0


class CacheAside(Generic[K, V]):
    """Load missing values once per key while concurrent callers wait."""

    def __init__(
        self,
        backend: CacheBackend[K, V],
        *,
        metrics: MetricRecorder | None = None,
        name: str = "default",
        timer: Callable[[], float] = perf_counter,
    ) -> None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Cache-aside name must not be blank.")
        self._backend = backend
        self._metrics = metrics or NoOpMetricsRegistry()
        self._name = normalized_name
        self._timer = timer
        self._flights: dict[K, _Flight] = {}
        self._guard = RLock()
        self._local = local()

    def get_or_load(
        self,
        key: K,
        loader: Callable[[], V],
        *,
        ttl_seconds: float | None = None,
    ) -> V:
        if not callable(loader):
            raise TypeError("Cache loader must be callable.")
        first = self._backend.get(key)
        if first.found:
            return cast(V, first.value)
        active = getattr(self._local, "active", set())
        if key in active:
            raise CacheLoadError(f"Re-entrant cache load detected for key {key!r}.")
        flight = self._join(key)
        try:
            with flight.lock:
                second = self._backend.get(key)
                if second.found:
                    return cast(V, second.value)
                started = self._timer()
                active = set(getattr(self._local, "active", set()))
                active.add(key)
                self._local.active = active
                try:
                    value = loader()
                except Exception as error:
                    self._metrics.increment(
                        "cache.load.failures", labels={"cache": self._name}
                    )
                    raise CacheLoadError(
                        f"Cache loader failed for key {key!r}: "
                        f"{type(error).__name__}: {error}"
                    ) from error
                finally:
                    active.remove(key)
                    self._local.active = active
                    self._metrics.observe(
                        "cache.load.duration",
                        max(0.0, self._timer() - started),
                        labels={"cache": self._name},
                    )
                self._backend.set(key, value, ttl_seconds=ttl_seconds)
                self._metrics.increment("cache.loads", labels={"cache": self._name})
                return value
        finally:
            self._leave(key, flight)

    def _join(self, key: K) -> _Flight:
        with self._guard:
            flight = self._flights.get(key)
            if flight is None:
                flight = _Flight(Lock())
                self._flights[key] = flight
            flight.users += 1
            return flight

    def _leave(self, key: K, flight: _Flight) -> None:
        with self._guard:
            flight.users -= 1
            if flight.users == 0 and self._flights.get(key) is flight:
                del self._flights[key]
