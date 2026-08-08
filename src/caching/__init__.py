import asyncio
import inspect
import threading
import time
from enum import Enum, auto
from typing import Generic, TypeVar, Optional, Dict, Any, Tuple, Callable, Set

K = TypeVar('K')
V = TypeVar('V')

class CacheError(Exception):
    """Base exception for caching errors."""
    pass

class CacheKeyError(CacheError, TypeError, KeyError):
    """Raised when a cache key is invalid or unhashable."""
    pass

class CacheLoadError(CacheError, RuntimeError):
    """Raised when cache loader fails or re-entrant load is detected."""
    pass

class EvictionPolicy(Enum):
    LRU = auto()
    FIFO = auto()

class CachePolicy:
    def __init__(
        self,
        ttl_seconds: Optional[float] = None,
        max_entries: Optional[int] = None,
        eviction: Any = EvictionPolicy.LRU,
        eviction_policy: Any = None,
    ):
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("TTL seconds must be > 0")
        if max_entries is not None and max_entries <= 0:
            raise ValueError("maximum entries must be > 0")
        ev = eviction_policy if eviction_policy is not None else eviction
        if ev is not None and not isinstance(ev, EvictionPolicy):
            raise TypeError("EvictionPolicy must be an instance of EvictionPolicy")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.eviction = ev
        self.eviction_policy = ev

class CacheStats:
    def __init__(
        self,
        entries: int = 0,
        hits: int = 0,
        misses: int = 0,
        expirations: int = 0,
        evictions: int = 0,
        writes: int = 0,
        deletes: int = 0,
    ):
        self.entries = entries
        self.hits = hits
        self.misses = misses
        self.expirations = expirations
        self.evictions = evictions
        self.writes = writes
        self.deletes = deletes

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class CacheGetResult(Generic[V]):
    def __init__(self, found: bool, value: Optional[V] = None):
        self.found = found
        self.value = value

class InMemoryCache(Generic[K, V]):
    def __init__(
        self,
        policy: Optional[CachePolicy] = None,
        clock: Optional[Callable[[], float]] = None,
        name: str = "default",
        metrics: Any = None,
    ):
        self.policy = policy or CachePolicy()
        self.clock = clock or time.time
        self.name = name
        self.metrics = metrics
        self._store: Dict[K, Tuple[V, float, Optional[float]]] = {}
        self._hits = 0
        self._misses = 0
        self._expirations = 0
        self._evictions = 0
        self._writes = 0
        self._deletes = 0

    def _update_entries_metric(self) -> None:
        if not self.metrics:
            return
        labels = {"cache": self.name}
        try:
            self.metrics.set_gauge("cache.entries", float(len(self._store)), labels=labels)
        except Exception:
            try:
                self.metrics.gauge("cache.entries", labels=labels).set(float(len(self._store)))
            except Exception:
                pass

    def _record_metric(self, name: str, amount: float = 1.0) -> None:
        if not self.metrics:
            return
        labels = {"cache": self.name}
        try:
            self.metrics.increment(name, amount, labels=labels)
        except Exception:
            try:
                self.metrics.counter(name, labels=labels).increment(amount)
            except Exception:
                pass

    def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        try:
            hash(key)
        except TypeError as e:
            raise CacheKeyError(f"Key {key} must be hashable") from e

        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("TTL seconds must be > 0")
        effective_ttl = ttl_seconds if ttl_seconds is not None else self.policy.ttl_seconds
        now = self.clock()
        expires_at = now + effective_ttl if effective_ttl else None
        
        self._writes += 1
        self._record_metric("cache.writes")

        # Purge expired entries
        expired_keys = [k for k, (_, _, exp) in list(self._store.items()) if exp and exp <= now]
        for ek in expired_keys:
            del self._store[ek]
            self._expirations += 1

        # Capacity eviction
        if self.policy.max_entries and len(self._store) >= self.policy.max_entries and key not in self._store:
            first_key = next(iter(self._store))
            del self._store[first_key]
            self._evictions += 1
            self._record_metric("cache.evictions")

        self._store[key] = (value, now, expires_at)
        self._update_entries_metric()

    def get(self, key: K) -> CacheGetResult[V]:
        try:
            hash(key)
        except TypeError as e:
            raise CacheKeyError(f"Key {key} must be hashable") from e

        now = self.clock()
        if key in self._store:
            val, created, expires_at = self._store[key]
            if expires_at and expires_at <= now:
                del self._store[key]
                self._expirations += 1
                self._misses += 1
                self._record_metric("cache.misses")
                return CacheGetResult(False, None)
            
            # LRU re-ordering
            if self.policy.eviction == EvictionPolicy.LRU:
                del self._store[key]
                self._store[key] = (val, created, expires_at)

            self._hits += 1
            self._record_metric("cache.hits")
            return CacheGetResult(True, val)

        self._misses += 1
        self._record_metric("cache.misses")
        return CacheGetResult(False, None)

    def delete(self, key: K) -> bool:
        self._deletes += 1
        if key in self._store:
            del self._store[key]
            self._update_entries_metric()
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
            expirations=self._expirations,
            evictions=self._evictions,
            writes=self._writes,
            deletes=self._deletes,
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
    def __init__(self, cache: Optional[InMemoryCache[K, V]] = None, loader: Optional[Callable] = None):
        self.cache = cache if cache is not None else InMemoryCache()
        self.loader = loader
        self._key_locks: Dict[Any, threading.Lock] = {}
        self._locks_lock = threading.Lock()
        self._in_flight = threading.local()

    def _get_key_lock(self, key: Any) -> threading.Lock:
        with self._locks_lock:
            if key not in self._key_locks:
                self._key_locks[key] = threading.Lock()
            return self._key_locks[key]

    def get_or_load(self, key: K, loader: Optional[Callable] = None) -> V:
        res = self.cache.get(key)
        if res.found:
            return res.value  # type: ignore

        if not hasattr(self._in_flight, "keys"):
            self._in_flight.keys = set()
        if key in self._in_flight.keys:
            raise CacheLoadError(f"Re-entrant load detected for key '{key}'")

        active_loader = loader or self.loader
        if active_loader is None:
            raise CacheLoadError("No loader provided")

        key_lock = self._get_key_lock(key)
        with key_lock:
            res = self.cache.get(key)
            if res.found:
                return res.value  # type: ignore

            self._in_flight.keys.add(key)
            try:
                try:
                    val = active_loader(key)
                except TypeError:
                    val = active_loader()
            except Exception as e:
                if isinstance(e, CacheLoadError):
                    raise
                raise CacheLoadError(str(e)) from e
            finally:
                self._in_flight.keys.remove(key)

            self.cache.set(key, val)
            return val

    def get(self, key: K, loader: Optional[Callable] = None) -> V:
        return self.get_or_load(key, loader)

    async def get_async(self, key: K, loader: Optional[Callable] = None) -> V:
        res = self.cache.get(key)
        if res.found:
            return res.value  # type: ignore

        active_loader = loader or self.loader
        if active_loader is None:
            raise CacheLoadError("No loader provided")

        if inspect.iscoroutinefunction(active_loader):
            try:
                val = await active_loader(key)
            except TypeError:
                val = await active_loader()
        else:
            try:
                val = active_loader(key)
            except TypeError:
                val = active_loader()

        self.cache.set(key, val)
        return val

    async def get_or_set(self, key: K, loader: Optional[Callable] = None) -> V:
        return await self.get_async(key, loader=loader)

__all__ = [
    "CacheError",
    "CacheKeyError",
    "CacheLoadError",
    "EvictionPolicy",
    "CachePolicy",
    "CacheStats",
    "CacheGetResult",
    "InMemoryCache",
    "NamespacedCache",
    "CacheAside",
]