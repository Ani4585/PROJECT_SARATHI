"""Collision-free cache namespaces."""

from __future__ import annotations

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import Generic, TypeVar, cast

from src.observability.contracts import MetricRecorder

from .aside import CacheAside
from .contracts import CacheBackend
from .model import CacheLookup, CacheStats


K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


@dataclass(frozen=True, slots=True)
class _NamespacedKey(Generic[K]):
    namespace: str
    key: K


class NamespacedCache(Generic[K, V]):
    def __init__(
        self,
        backend: CacheBackend[Hashable, V],
        namespace: str,
        *,
        metrics: MetricRecorder | None = None,
    ) -> None:
        normalized = namespace.strip()
        if not normalized:
            raise ValueError("Cache namespace must not be blank.")
        self._backend = backend
        self._namespace = normalized
        self._aside: CacheAside[Hashable, V] = CacheAside(
            backend,
            metrics=metrics,
            name=normalized,
        )

    @property
    def namespace(self) -> str:
        return self._namespace

    def get(self, key: K) -> CacheLookup[V]:
        return self._backend.get(self._key(key))

    def set(self, key: K, value: V, *, ttl_seconds: float | None = None) -> None:
        self._backend.set(self._key(key), value, ttl_seconds=ttl_seconds)

    def delete(self, key: K) -> bool:
        return self._backend.delete(self._key(key))

    def get_or_load(
        self,
        key: K,
        loader: Callable[[], V],
        *,
        ttl_seconds: float | None = None,
    ) -> V:
        return self._aside.get_or_load(
            self._key(key),
            loader,
            ttl_seconds=ttl_seconds,
        )

    def clear(self) -> int:
        keys = tuple(
            key
            for key in self._backend.keys()
            if isinstance(key, _NamespacedKey) and key.namespace == self._namespace
        )
        return sum(self._backend.delete(key) for key in keys)

    def keys(self) -> tuple[K, ...]:
        return tuple(
            cast(_NamespacedKey[K], key).key
            for key in self._backend.keys()
            if isinstance(key, _NamespacedKey) and key.namespace == self._namespace
        )

    def stats(self) -> CacheStats:
        return self._backend.stats()

    def _key(self, key: K) -> _NamespacedKey[K]:
        return _NamespacedKey(self._namespace, key)
