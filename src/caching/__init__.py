import asyncio
import time
from enum import Enum, auto
from typing import Generic, TypeVar, Optional, Dict, Any, Tuple, Callable

K = TypeVar('K')
V = TypeVar('V')

class CacheKeyError(KeyError):
    """Raised when a cache key is invalid or not found."""
    pass

class EvictionPolicy(Enum):
    LRU = auto()
    FIFO = auto()

class CachePolicy:
    def __init__(self, ttl_seconds: Optional[float] = None, max_entries: Optional[int] = None, eviction_policy: Any = EvictionPolicy.LRU):
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("TTL seconds must be > 0")
        if max_entries is not None and max_entries <= 0:
            raise ValueError("maximum entries must be > 0")
        if eviction_policy is not None and not isinstance(eviction_policy, EvictionPolicy):
            raise TypeError("EvictionPolicy expected")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.eviction_policy = eviction_policy

class CacheStats:
    def __init__(self, entries: int = 0, hits: int = 0, misses: int = 0, expirations: int = 0, evictions: int = 0):
        self.entries = entries
        self.hits = hits
        self.misses = misses
        self.expirations = expirations
        self.evictions = evictions

class CacheGetResult(Generic[V]):
    def __init__(self, found: bool, value: Optional[V] = None):
        self.found = found
        self.value = value

class InMemoryCache(Generic[K, V]):
    def __init__(self, policy: Optional[CachePolicy] = None, clock: Optional[Callable[[], float]] = None, name: str = "default", metrics: Any = None):
        self.policy = policy or CachePolicy()
        self.clock = clock or time.time
        self.name = name
        self.metrics = metrics
        self._store: Dict[K, Tuple[V, float, Optional[float]]] = {}
        self._hits = 0
        self._misses = 0
        self._expirations = 0

    def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("TTL seconds must be > 0")
        effective_ttl = ttl_seconds if ttl_seconds is not None else self.policy.ttl_seconds
        now = self.clock()
        expires_at = now + effective_ttl if effective_ttl else None
        
        # Purge expired entries
        expired_keys = [k for k, (_, _, exp) in list(self._store.items()) if exp and exp <= now]
        for ek in expired_keys:
            del self._store[ek]
            self._expirations += 1

        # Capacity eviction
        if self.policy.max_entries and len(self._store) >= self.policy.max_entries and key not in self._store:
            first_key = next(iter(self._store))
            del self._store[first_key]

        self._store[key] = (value, now, expires_at)

    def get(self, key: K) -> CacheGetResult[V]:
        now = self.clock()
        labels = (("cache", self.name),)
        if key in self._store:
            val, created, expires_at = self._store[key]
            if expires_at and expires_at <= now:
                del self._store[key]
                self._expirations += 1
                self._misses += 1
                if self.metrics:
                    try:
                        self.metrics.counter("cache.misses", labels=labels).increment()
                    except Exception:
                        pass
                return CacheGetResult(False, None)
            self._hits += 1
            if self.metrics:
                try:
                    self.metrics.counter("cache.hits", labels=labels).increment()
                except Exception:
                    pass
            return CacheGetResult(True, val)
        self._misses += 1
        if self.metrics:
            try:
                self.metrics.counter("cache.misses", labels=labels).increment()
            except Exception:
                pass
        return CacheGetResult(False, None)

    def delete(self, key: K) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count

    def keys(self) -> Tuple[K, ...]:
        return tuple(self._store.keys())

    def stats(self) -> CacheStats:
        return CacheStats(
            entries=len(self._store),
            hits=self._hits,
            misses=self._misses,
            expirations=self._expirations
        )

class NamespacedCache(Generic[K, V]):
    def __init__(self, backend: InMemoryCache[Any, V], namespace: str):
        self.backend = backend
        self.namespace = namespace

    def _make_key(self, key: K) -> str:
        return f"{self.namespace}:{key}"

    def set(self, key: K, value: V, ttl_seconds: Any = None) -> None:
        self.backend.set(self._make_key(key), value, ttl_seconds)

    def get(self, key: K) -> CacheGetResult[V]:
        return self.backend.get(self._make_key(key))

    def keys(self) -> Tuple[K, ...]:
        prefix = f"{self.namespace}:"
        return tuple(k[len(prefix):] for k in self.backend.keys() if str(k).startswith(prefix))

    def clear(self) -> int:
        prefix = f"{self.namespace}:"
        matching_keys = [k for k in self.backend.keys() if str(k).startswith(prefix)]
        for k in matching_keys:
            self.backend.delete(k)
        return len(matching_keys)

class CacheAside(Generic[K, V]):
    def __init__(self, cache: InMemoryCache[K, V], loader: Callable[[K], Any]):
        self.cache = cache
        self.loader = loader

    def get(self, key: K) -> V:
        res = self.cache.get(key)
        if res.found:
            return res.value  # type: ignore
        val = self.loader(key)
        self.cache.set(key, val)
        return val

    async def get_async(self, key: K) -> V:
        res = self.cache.get(key)
        if res.found:
            return res.value  # type: ignore
        if asyncio.iscoroutinefunction(self.loader):
            val = await self.loader(key)
        else:
            val = self.loader(key)
        self.cache.set(key, val)
        return val

__all__ = [
    "CacheKeyError",
    "EvictionPolicy",
    "CachePolicy",
    "CacheStats",
    "CacheGetResult",
    "InMemoryCache",
    "NamespacedCache",
    "CacheAside",
]