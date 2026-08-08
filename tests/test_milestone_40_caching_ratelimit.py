import pytest
import asyncio
from src.caching.distributed import DistributedCacheStore
from src.caching import CacheAside
from src.resilience.rate_limiter import TokenBucketRateLimiter
from src.caching.decorators import cached

def test_cache_ttl_expiration():
    async def _test():
        cache = DistributedCacheStore(max_size=10)
        await cache.set("k1", "v1", ttl_seconds=0.05)
        assert await cache.get("k1") == "v1"
        await asyncio.sleep(0.06)
        assert await cache.get("k1") is None
    asyncio.run(_test())

def test_cache_lru_eviction():
    async def _test():
        cache = DistributedCacheStore(max_size=2)
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.set("c", 3)
        assert cache.size() == 2
        assert await cache.get("a") is None
        assert await cache.get("b") == 2
        assert await cache.get("c") == 3
    asyncio.run(_test())

def test_cache_aside_pattern():
    async def _test():
        ca = CacheAside()
        val = await ca.get_or_set("item_1", lambda: "Data 1")
        assert val == "Data 1"
        val_cached = await ca.get_or_set("item_1", lambda: "Data 2")
        assert val_cached == "Data 1"
    asyncio.run(_test())

def test_token_bucket_rate_limiter():
    async def _test():
        limiter = TokenBucketRateLimiter(capacity=2, refill_rate_per_sec=10)
        assert await limiter.acquire(1) is True
        assert await limiter.acquire(1) is True
        assert await limiter.acquire(1) is False
    asyncio.run(_test())

def test_cached_decorator():
    async def _test():
        call_count = 0
        @cached(ttl_seconds=10)
        async def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        res1 = await compute(5)
        res2 = await compute(5)
        assert res1 == 10
        assert res2 == 10
        assert call_count == 1
    asyncio.run(_test())
