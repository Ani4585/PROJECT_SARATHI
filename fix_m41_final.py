import os
import sys
from pathlib import Path

def write_file(path_str: str, content: str):
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"[UPDATED] {path_str}")

# 1. Update sarathi/__init__.py and src/sarathi/__init__.py
SARATHI_INIT = '''
import sys
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_root_dir = str(_pkg_dir.parent.parent if _pkg_dir.parent.name == "src" else _pkg_dir.parent)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from scripts.tooling.cli.application import create_cli_application, main

from . import caching, ratelimit, resilience, telemetry

__all__ = [
    "create_cli_application",
    "main",
    "caching",
    "ratelimit",
    "resilience",
    "telemetry",
]
'''

write_file("sarathi/__init__.py", SARATHI_INIT)
write_file("src/sarathi/__init__.py", SARATHI_INIT)

# 2. Update two_level.py to use inspect.iscoroutinefunction (removes deprecation warnings)
TWO_LEVEL_CACHE_CODE = '''
import asyncio
import inspect
import time
from typing import Any, Callable, Dict, Optional, Tuple

class DistributedCacheConfig:
    def __init__(
        self,
        l1_ttl: float = 60.0,
        l2_ttl: float = 300.0,
        bypass_on_l2_error: bool = True,
        enable_metrics: bool = True
    ):
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        self.bypass_on_l2_error = bypass_on_l2_error
        self.enable_metrics = enable_metrics

class TwoLevelCache:
    """
    Two-Level Distributed Cache Architecture (L1 Local Memory + L2 Distributed Store)
    with Cache Stampede Protection (SingleFlight per key) and Fallback Bypass Resilience.
    """
    def __init__(
        self,
        l2_backend: Optional[Any] = None,
        config: Optional[DistributedCacheConfig] = None,
        l1_ttl: float = 60.0,
        l2_ttl: float = 300.0,
        bypass_on_l2_error: bool = True
    ):
        if config:
            self.l1_ttl = config.l1_ttl
            self.l2_ttl = config.l2_ttl
            self.bypass_on_l2_error = config.bypass_on_l2_error
        else:
            self.l1_ttl = l1_ttl
            self.l2_ttl = l2_ttl
            self.bypass_on_l2_error = bypass_on_l2_error

        self.l2_backend = l2_backend
        self.l1_store: Dict[str, Tuple[Any, float]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._locks_lock = asyncio.Lock()

        self.metrics = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "l2_errors": 0,
            "stampede_blocked": 0,
            "loader_calls": 0,
            "invalidations": 0
        }

    def _get_l1(self, key: str) -> Tuple[bool, Any]:
        now = time.monotonic()
        if key in self.l1_store:
            val, exp = self.l1_store[key]
            if exp is None or exp > now:
                return True, val
            else:
                del self.l1_store[key]
        return False, None

    def _set_l1(self, key: str, value: Any, ttl: Optional[float] = None):
        effective_ttl = ttl if ttl is not None else self.l1_ttl
        exp = time.monotonic() + effective_ttl if effective_ttl > 0 else None
        self.l1_store[key] = (value, exp)

    async def get(self, key: str) -> Optional[Any]:
        hit, val = self._get_l1(key)
        if hit:
            self.metrics["l1_hits"] += 1
            return val
        self.metrics["l1_misses"] += 1

        if self.l2_backend is not None:
            try:
                if inspect.iscoroutinefunction(getattr(self.l2_backend, "get", None)):
                    val = await self.l2_backend.get(key)
                elif hasattr(self.l2_backend, "get"):
                    val = self.l2_backend.get(key)
                else:
                    val = None

                if val is not None:
                    self.metrics["l2_hits"] += 1
                    self._set_l1(key, val)
                    return val
                self.metrics["l2_misses"] += 1
            except Exception as e:
                self.metrics["l2_errors"] += 1
                if not self.bypass_on_l2_error:
                    raise e

        return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        if self.l2_backend is not None:
            try:
                effective_l2_ttl = ttl if ttl is not None else self.l2_ttl
                if inspect.iscoroutinefunction(getattr(self.l2_backend, "set", None)):
                    await self.l2_backend.set(key, value, effective_l2_ttl)
                elif hasattr(self.l2_backend, "set"):
                    self.l2_backend.set(key, value, effective_l2_ttl)
            except Exception as e:
                self.metrics["l2_errors"] += 1
                if not self.bypass_on_l2_error:
                    raise e

        self._set_l1(key, value, ttl)

    async def invalidate(self, key: str) -> None:
        self.metrics["invalidations"] += 1
        self.l1_store.pop(key, None)
        if self.l2_backend is not None:
            try:
                if inspect.iscoroutinefunction(getattr(self.l2_backend, "delete", None)):
                    await self.l2_backend.delete(key)
                elif hasattr(self.l2_backend, "delete"):
                    self.l2_backend.delete(key)
            except Exception:
                self.metrics["l2_errors"] += 1

    async def get_or_load(self, key: str, loader: Callable[[], Any], ttl: Optional[float] = None) -> Any:
        val = await self.get(key)
        if val is not None:
            return val

        async with self._locks_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            key_lock = self._locks[key]

        async with key_lock:
            hit, val = self._get_l1(key)
            if hit:
                self.metrics["stampede_blocked"] += 1
                return val

            if self.l2_backend is not None:
                try:
                    if inspect.iscoroutinefunction(getattr(self.l2_backend, "get", None)):
                        val = await self.l2_backend.get(key)
                    elif hasattr(self.l2_backend, "get"):
                        val = self.l2_backend.get(key)
                    
                    if val is not None:
                        self.metrics["stampede_blocked"] += 1
                        self._set_l1(key, val, ttl)
                        return val
                except Exception:
                    self.metrics["l2_errors"] += 1

            self.metrics["loader_calls"] += 1
            if inspect.iscoroutinefunction(loader):
                val = await loader()
            else:
                val = loader()
                if asyncio.iscoroutine(val):
                    val = await val

            await self.set(key, val, ttl)
            return val

DistributedCache = TwoLevelCache
'''

write_file("sarathi/caching/two_level.py", TWO_LEVEL_CACHE_CODE)
write_file("src/sarathi/caching/two_level.py", TWO_LEVEL_CACHE_CODE)

print("Final tuning completed!")
