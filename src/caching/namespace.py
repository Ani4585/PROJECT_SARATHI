from typing import Generic, TypeVar, Any, Tuple
from .memory import InMemoryCache, CacheGetResult

K = TypeVar('K')
V = TypeVar('V')

class NamespacedCache(Generic[K, V]):
    def __init__(self, backend: InMemoryCache[Any, V], namespace: str):
        self.backend = backend
        self.namespace = namespace

    def _make_key(self, key: K) -> str:
        return f"{self.namespace}:{key}"

    def set(self, key: K, value: V, ttl_seconds: Any = None) -> None:
        self.backend.set(self._make_key(key), value, ttl_seconds)

    def get(self, key: K) -> CacheGetResult:
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