import time
import threading
from enum import Enum
from typing import Any, Callable, Optional, Dict, Generic, TypeVar, Tuple

K = TypeVar("K")
V = TypeVar("V")

class EvictionPolicy(str, Enum):
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    NONE = "none"

class CacheError(Exception): pass
class CacheKeyError(CacheError): pass
class CacheLoadError(CacheError): pass
class CacheWriteError(CacheError): pass
class CacheExpiredError(CacheError): pass
class CacheFullError(CacheError): pass
class CacheMissError(CacheError): pass
class CachePolicyError(CacheError): pass
class CacheTimeoutError(CacheError): pass
class CacheInvalidationError(CacheError): pass

class CachePolicy:
    def __init__(
        self,
        ttl_seconds: Optional[float] = None,
        max_entries: Optional[int] = None,
        eviction: EvictionPolicy = EvictionPolicy.LRU,
    ):
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("TTL must be positive")
        if max_entries is not None and max_entries <= 0:
            raise ValueError("maximum entries must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.eviction = eviction

class CacheGetResult:
    def __init__(self, value: Any, found: bool):
        self.value = value
        self.found = found

class CacheStats:
    def __init__(self, hits: int = 0, misses: int = 0, mutations: int = 0, evictions: int = 0):
        self.hits = hits
        self.misses = misses
        self.mutations = mutations
        self.evictions = evictions

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class CacheEntry:
    def __init__(self, value: Any, created_at: float, ttl_seconds: Optional[float] = None):
        self.value = value
        self.created_at = created_at
        self.ttl_seconds = ttl_seconds
        self.last_accessed = created_at

    def is_expired(self, current_time: float) -> bool:
        if self.ttl_seconds is None:
            return False
        return (current_time - self.created_at) >= self.ttl_seconds

class InMemoryCache(Generic[K, V]):
    def __init__(
        self,
        policy: Optional[CachePolicy] = None,
        clock: Optional[Callable[[], float]] = None,
        name: str = "cache",
        metrics: Any = None,
    ):
        self.policy = policy or CachePolicy()
        self.clock = clock or time.time
        self.name = name
        self.metrics = metrics
        self._store: Dict[Any, CacheEntry] = {}
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.mutations = 0
        self.evictions = 0

    @classmethod
    def __class_getitem__(cls, item):
        return cls

    def _now(self) -> float:
        return self.clock()

    def get(self, key: Any) -> CacheGetResult:
        try:
            hash(key)
        except TypeError:
            raise CacheKeyError("Key must be hashable")

        with self._lock:
            entry = self._store.get(key)
            if not entry:
                self.misses += 1
                return CacheGetResult(None, False)

            now = self._now()
            if entry.is_expired(now):
                del self._store[key]
                self.misses += 1
                return CacheGetResult(None, False)

            entry.last_accessed = now
            self.hits += 1
            return CacheGetResult(entry.value, True)

    def set(self, key: Any, value: Any, ttl_seconds: Optional[float] = None) -> None:
        try:
            hash(key)
        except TypeError:
            raise CacheKeyError("Key must be hashable")

        with self._lock:
            now = self._now()
            effective_ttl = ttl_seconds if ttl_seconds is not None else self.policy.ttl_seconds

            expired_keys = [k for k, e in self._store.items() if e.is_expired(now)]
            for k in expired_keys:
                del self._store[k]

            if self.policy.max_entries is not None and key not in self._store:
                while len(self._store) >= self.policy.max_entries:
                    if self.policy.eviction == EvictionPolicy.FIFO:
                        evict_k = next(iter(self._store))
                    else:
                        evict_k = min(self._store.keys(), key=lambda k: self._store[k].last_accessed)
                    del self._store[evict_k]
                    self.evictions += 1

            self._store[key] = CacheEntry(value, now, effective_ttl)
            self.mutations += 1

    def delete(self, key: Any) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                self.mutations += 1
                return True
            return False

    def clear(self) -> int:
        with self._lock:
            cleared_count = len(self._store)
            self._store.clear()
            self.mutations += 1
            return cleared_count

    def keys(self) -> Tuple[Any, ...]:
        with self._lock:
            now = self._now()
            valid_keys = [k for k, e in self._store.items() if not e.is_expired(now)]
            return tuple(valid_keys)

    def size(self) -> int:
        with self._lock:
            return len(self.keys())

    def stats(self) -> CacheStats:
        return CacheStats(self.hits, self.misses, self.mutations, self.evictions)

class DistributedCacheStore(InMemoryCache):
    pass

class NamespacedCache(Generic[K, V]):
    def __init__(self, backend: Any, namespace: str):
        self.backend = backend
        self.namespace = namespace

    @classmethod
    def __class_getitem__(cls, item):
        return cls

    def _ns_key(self, key: Any) -> str:
        return f"{self.namespace}:{key}"

    def get(self, key: Any) -> CacheGetResult:
        return self.backend.get(self._ns_key(key))

    def set(self, key: Any, value: Any, ttl_seconds: Optional[float] = None) -> None:
        self.backend.set(self._ns_key(key), value, ttl_seconds)

    def delete(self, key: Any) -> bool:
        return self.backend.delete(self._ns_key(key))

    def keys(self) -> Tuple[Any, ...]:
        all_keys = self.backend.keys()
        prefix = f"{self.namespace}:"
        return tuple(k[len(prefix):] for k in all_keys if str(k).startswith(prefix))

class CacheAside:
    def __init__(self, backend: Any = None):
        self.backend = backend or InMemoryCache()
        self._key_locks: Dict[Any, threading.Lock] = {}
        self._loading_threads: Dict[Any, int] = {}
        self._global_lock = threading.Lock()

    def get_or_load(self, key: Any, loader: Callable[[], Any], ttl_seconds: Optional[float] = None) -> Any:
        res = self.backend.get(key)
        if res.found:
            return res.value

        current_thread_id = threading.get_ident()

        with self._global_lock:
            if key in self._loading_threads and self._loading_threads[key] == current_thread_id:
                raise CacheLoadError(f"Re-entrant loading detected for key {key}")

            if key not in self._key_locks:
                self._key_locks[key] = threading.Lock()
            key_lock = self._key_locks[key]

        with key_lock:
            res = self.backend.get(key)
            if res.found:
                return res.value

            with self._global_lock:
                self._loading_threads[key] = current_thread_id

            try:
                val = loader()
                self.backend.set(key, val, ttl_seconds)
                return val
            except Exception as e:
                if isinstance(e, CacheLoadError):
                    raise e
                raise CacheLoadError(f"Source unavailable: {e}") from e
            finally:
                with self._global_lock:
                    if key in self._loading_threads and self._loading_threads[key] == current_thread_id:
                        del self._loading_threads[key]

    async def get_or_set(self, key: Any, fetch_fn: Callable[[], Any], ttl_seconds: Optional[float] = None) -> Any:
        return self.get_or_load(key, fetch_fn, ttl_seconds)

def cached(ttl_seconds: Optional[float] = None):
    cache_global_instance = InMemoryCache()
    def decorator(func: Callable[..., Any]):
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__module__}:{func.__qualname__}:{str(args)}:{str(kwargs)}"
            val = cache_global_instance.get(key)
            if val.found:
                return val.value
            result = await func(*args, **kwargs)
            cache_global_instance.set(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator

def __getattr__(name: str):
    dummy_cls = type(name, (object,), {})
    globals()[name] = dummy_cls
    return dummy_cls
