import functools
import inspect
from typing import Callable, Any

def fallback(fallback_handler: Any):
    def decorator(fn: Callable):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    if callable(fallback_handler):
                        if inspect.iscoroutinefunction(fallback_handler):
                            return await fallback_handler(*args, **kwargs)
                        else:
                            sig = inspect.signature(fallback_handler)
                            if len(sig.parameters) == 1 and 'exc' in sig.parameters:
                                return fallback_handler(exc)
                            try:
                                return fallback_handler(*args, **kwargs)
                            except TypeError:
                                return fallback_handler()
                    return fallback_handler
            return wrapper
        else:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if callable(fallback_handler):
                        sig = inspect.signature(fallback_handler)
                        if len(sig.parameters) == 1 and 'exc' in sig.parameters:
                            return fallback_handler(exc)
                        try:
                            return fallback_handler(*args, **kwargs)
                        except TypeError:
                            return fallback_handler()
                    return fallback_handler
            return wrapper
    return decorator
