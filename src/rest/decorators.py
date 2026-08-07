"""PROJECT SARATHI REST Controller and Route Decorators."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def controller(prefix: str = "") -> Callable[[type[T]], type[T]]:
    """Mark a class as a REST Controller with an optional path prefix."""

    def decorator(cls: type[T]) -> type[T]:
        setattr(cls, "__is_controller__", True)
        setattr(cls, "__controller_prefix__", prefix.rstrip("/"))
        return cls

    return decorator


def _route(method: str, path: str = "") -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        setattr(func, "__route_method__", method.upper())
        setattr(func, "__route_path__", path if path.startswith("/") or not path else f"/{path}")
        return func

    return decorator


def get(path: str = "") -> Callable[[Callable], Callable]:
    return _route("GET", path)


def post(path: str = "") -> Callable[[Callable], Callable]:
    return _route("POST", path)


def put(path: str = "") -> Callable[[Callable], Callable]:
    return _route("PUT", path)


def delete(path: str = "") -> Callable[[Callable], Callable]:
    return _route("DELETE", path)


def patch(path: str = "") -> Callable[[Callable], Callable]:
    return _route("PATCH", path)
