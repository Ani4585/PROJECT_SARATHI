import time
from typing import Any, Dict, Optional

class CacheEntry:
    def __init__(self, value: Any, ttl_seconds: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

class DistributedCacheStore:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._store: Dict[str, CacheEntry] = {}

    async def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        if len(self._store) >= self.max_size and key not in self._store:
            first_key = next(iter(self._store))
            del self._store[first_key]
        self._store[key] = CacheEntry(value, ttl_seconds)

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)
