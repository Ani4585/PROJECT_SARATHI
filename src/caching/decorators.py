from typing import Any, Callable, Optional
from src.caching.distributed import DistributedCacheStore

cache_global_instance = DistributedCacheStore()

def cached(ttl_seconds: Optional[float] = None):
    def decorator(func: Callable[..., Any]):
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__module__}:{func.__qualname__}:{str(args)}:{str(kwargs)}"
            val = await cache_global_instance.get(key)
            if val is not None:
                return val
            result = await func(*args, **kwargs)
            await cache_global_instance.set(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator
