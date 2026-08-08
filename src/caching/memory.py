import time
from typing import Generic, TypeVar, Optional, Dict, Any, Tuple, Callable
from .model import CachePolicy, CacheStats, CacheGetResult

K = TypeVar('K')
V = TypeVar('V')

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
        
        # Purge expired entries first
        expired_keys = [k for k, (_, _, exp) in list(self._store.items()) if exp and exp <= now]
        for ek in expired_keys:
            del self._store[ek]
            self._expirations += 1

        # Evict for max entries capacity
        if self.policy.max_entries and len(self._store) >= self.policy.max_entries and key not in self._store:
            first_key = next(iter(self._store))
            del self._store[first_key]

        self._store[key] = (value, now, expires_at)

    def get(self, key: K) -> CacheGetResult:
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