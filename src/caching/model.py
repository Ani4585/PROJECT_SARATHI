from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Any

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

@dataclass
class CacheStats:
    entries: int = 0
    hits: int = 0
    misses: int = 0
    expirations: int = 0
    evictions: int = 0

class CacheGetResult:
    def __init__(self, found: bool, value: Any = None):
        self.found = found
        self.value = value