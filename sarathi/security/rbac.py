import asyncio
import functools
import inspect
from typing import Callable, Set
from .models import UserIdentity, AuthenticationError, AuthorizationError, _SECURITY_CONTEXT

class Role:
    def __init__(self, name: str, permissions: Optional[Set[str]] = None):
        self.name = name
        self.permissions = permissions or set()

class Permission:
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"

def require_auth(fn: Callable):
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            user = _SECURITY_CONTEXT.get()
            if not user or not user.is_authenticated:
                raise AuthenticationError("Authentication required")
            return await fn(*args, **kwargs)
        return wrapper
    else:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user = _SECURITY_CONTEXT.get()
            if not user or not user.is_authenticated:
                raise AuthenticationError("Authentication required")
            return fn(*args, **kwargs)
        return wrapper

def require_role(role: str):
    def decorator(fn: Callable):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                user = _SECURITY_CONTEXT.get()
                if not user or not user.is_authenticated:
                    raise AuthenticationError("Authentication required")
                if not user.has_role(role):
                    raise AuthorizationError(f"User lacks required role '{role}'")
                return await fn(*args, **kwargs)
            return wrapper
        else:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                user = _SECURITY_CONTEXT.get()
                if not user or not user.is_authenticated:
                    raise AuthenticationError("Authentication required")
                if not user.has_role(role):
                    raise AuthorizationError(f"User lacks required role '{role}'")
                return fn(*args, **kwargs)
            return wrapper
    return decorator

def require_permission(permission: str):
    def decorator(fn: Callable):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                user = _SECURITY_CONTEXT.get()
                if not user or not user.is_authenticated:
                    raise AuthenticationError("Authentication required")
                if not user.has_permission(permission):
                    raise AuthorizationError(f"User lacks required permission '{permission}'")
                return await fn(*args, **kwargs)
            return wrapper
        else:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                user = _SECURITY_CONTEXT.get()
                if not user or not user.is_authenticated:
                    raise AuthenticationError("Authentication required")
                if not user.has_permission(permission):
                    raise AuthorizationError(f"User lacks required permission '{permission}'")
                return fn(*args, **kwargs)
            return wrapper
    return decorator
