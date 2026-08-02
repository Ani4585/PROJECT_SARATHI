"""Reusable route groups with path and name prefixes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .exceptions import InvalidRouteError


def join_paths(*paths: str) -> str:
    segments: list[str] = []
    for path in paths:
        if not isinstance(path, str):
            raise TypeError("Route prefixes and paths must be strings.")
        if path in ("", "/"):
            continue
        if not path.startswith("/") or path.endswith("/") or "//" in path:
            raise InvalidRouteError("Route prefix and group path must be absolute and clean.")
        segments.append(path.strip("/"))
    return "/" + "/".join(segments) if segments else "/"


@dataclass(frozen=True, slots=True)
class GroupRoute:
    path: str
    handler: Callable[..., object]
    methods: tuple[str, ...]
    name: str | None


class RouteGroup:
    """Collect route definitions before including them in a router."""

    def __init__(self, prefix: str = "", *, name_prefix: str = "") -> None:
        self.prefix = "" if prefix == "" else join_paths(prefix)
        if not isinstance(name_prefix, str):
            raise TypeError("Route group name prefix must be a string.")
        self.name_prefix = name_prefix
        self._routes: list[GroupRoute] = []

    @property
    def routes(self) -> tuple[GroupRoute, ...]:
        return tuple(self._routes)

    def add(
        self,
        path: str,
        handler: Callable[..., object],
        *,
        methods: Sequence[str] = ("GET",),
        name: str | None = None,
    ) -> GroupRoute:
        if not callable(handler):
            raise TypeError("Route group handler must be callable.")
        clean_path = join_paths(path)
        definition = GroupRoute(clean_path, handler, tuple(methods), name)
        self._routes.append(definition)
        return definition

    def route(
        self,
        path: str,
        *,
        methods: Sequence[str] = ("GET",),
        name: str | None = None,
    ) -> Callable[[Callable[..., object]], Callable[..., object]]:
        def decorator(handler: Callable[..., object]) -> Callable[..., object]:
            self.add(path, handler, methods=methods, name=name)
            return handler

        return decorator
