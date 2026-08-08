import asyncio
import functools
import inspect
from typing import Callable
from .models import TenantContextError, _TENANT_CONTEXT

def require_tenant(fn: Callable):
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            tenant = _TENANT_CONTEXT.get()
            if not tenant:
                raise TenantContextError("Tenant context required")
            return await fn(*args, **kwargs)
        return wrapper
    else:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            tenant = _TENANT_CONTEXT.get()
            if not tenant:
                raise TenantContextError("Tenant context required")
            return fn(*args, **kwargs)
        return wrapper
