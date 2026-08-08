import asyncio
import functools
import inspect
from typing import Callable, Dict, Optional, Union, Any
from .models import RateLimitResult, RateLimitExceededException
from .algorithms import TokenBucket, SlidingWindowCounter, LeakyBucket

class InMemoryRateLimiter:
    def __init__(self, limit: int = 10, period: float = 60.0, algorithm: str = "token_bucket"):
        self.limit = limit
        self.period = period
        self.algorithm = algorithm
        self.buckets: Dict[str, Union[TokenBucket, SlidingWindowCounter, LeakyBucket]] = {}
        self._async_lock: Optional[asyncio.Lock] = None
        self.metrics = {"allowed": 0, "rejected": 0}

    @property
    def async_lock(self) -> asyncio.Lock:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock

    def _get_bucket(self, key: str):
        if key not in self.buckets:
            if self.algorithm == "sliding_window":
                self.buckets[key] = SlidingWindowCounter(self.limit, self.period)
            elif self.algorithm == "leaky_bucket":
                leak_rate = float(self.limit) / float(self.period)
                self.buckets[key] = LeakyBucket(self.limit, leak_rate)
            else:
                refill_rate = float(self.limit) / float(self.period)
                self.buckets[key] = TokenBucket(self.limit, refill_rate)
        return self.buckets[key]

    def acquire(self, key: str = "default", tokens: int = 1) -> RateLimitResult:
        bucket = self._get_bucket(key)
        allowed, remaining, wait_time = bucket.consume(tokens)
        if allowed:
            self.metrics["allowed"] += 1
            retry_after = 0.0
            reset_after = wait_time
        else:
            self.metrics["rejected"] += 1
            retry_after = wait_time
            reset_after = wait_time

        return RateLimitResult(
            allowed=allowed,
            limit=self.limit,
            remaining=remaining,
            reset_after=reset_after,
            retry_after=retry_after
        )

    async def acquire_async(self, key: str = "default", tokens: int = 1) -> RateLimitResult:
        async with self.async_lock:
            return self.acquire(key, tokens)

class DistributedRateLimiter:
    def __init__(self, backend_store: Optional[Any] = None, limit: int = 10, period: float = 60.0):
        self.backend_store = backend_store
        self.fallback_limiter = InMemoryRateLimiter(limit=limit, period=period)
        self.limit = limit
        self.period = period
        self.metrics = {"allowed": 0, "rejected": 0, "backend_errors": 0}

    async def acquire_async(self, key: str = "default", tokens: int = 1) -> RateLimitResult:
        if self.backend_store is not None:
            try:
                if hasattr(self.backend_store, "acquire"):
                    res = await self.backend_store.acquire(key, tokens)
                    if res.allowed:
                        self.metrics["allowed"] += 1
                    else:
                        self.metrics["rejected"] += 1
                    return res
            except Exception:
                self.metrics["backend_errors"] += 1

        res = await self.fallback_limiter.acquire_async(key, tokens)
        if res.allowed:
            self.metrics["allowed"] += 1
        else:
            self.metrics["rejected"] += 1
        return res

    def acquire(self, key: str = "default", tokens: int = 1) -> RateLimitResult:
        res = self.fallback_limiter.acquire(key, tokens)
        if res.allowed:
            self.metrics["allowed"] += 1
        else:
            self.metrics["rejected"] += 1
        return res

def rate_limit(limiter: Union[InMemoryRateLimiter, DistributedRateLimiter], key_func: Optional[Callable] = None):
    def decorator(fn: Callable):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                key = key_func(*args, **kwargs) if key_func else "default"
                res = await limiter.acquire_async(key)
                if not res.allowed:
                    raise RateLimitExceededException(
                        f"Rate limit exceeded for key '{key}'. Retry after {res.retry_after:.2f}s", res
                    )
                return await fn(*args, **kwargs)
            return wrapper
        else:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                key = key_func(*args, **kwargs) if key_func else "default"
                res = limiter.acquire(key)
                if not res.allowed:
                    raise RateLimitExceededException(
                        f"Rate limit exceeded for key '{key}'. Retry after {res.retry_after:.2f}s", res
                    )
                return fn(*args, **kwargs)
            return wrapper
    return decorator
