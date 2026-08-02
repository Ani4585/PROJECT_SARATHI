"""Deterministic route registry and resolution."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from .converters import ConverterRegistry
from .exceptions import (
    InvalidRouteError,
    MethodNotAllowedError,
    RouteConflictError,
    RouteNotFoundError,
    ReverseRouteError,
)
from .group import RouteGroup, join_paths
from .route import Route, RouteMatch


_METHOD = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


class Router:
    """Register routes and resolve the most specific path match."""

    def __init__(self, *, converters: ConverterRegistry | None = None) -> None:
        self.converters = converters or ConverterRegistry.defaults()
        self._routes: list[Route] = []
        self._names: dict[str, Route] = {}

    @property
    def routes(self) -> tuple[Route, ...]:
        return tuple(self._routes)

    def add(
        self,
        path: str,
        handler: Callable[..., object],
        *,
        methods: Sequence[str] = ("GET",),
        name: str | None = None,
    ) -> Route:
        route = Route(
            path,
            handler,
            methods=methods,
            name=name,
            converters=self.converters,
        )
        self.register(route)
        return route

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

    def register(self, route: Route) -> None:
        if not isinstance(route, Route):
            raise TypeError("Router accepts Route instances.")
        if route.name is not None and route.name in self._names:
            raise RouteConflictError(f"Duplicate route name: {route.name!r}.")
        for existing in self._routes:
            overlapping = tuple(sorted(set(existing.methods) & set(route.methods)))
            if existing.signature == route.signature and overlapping:
                raise RouteConflictError(
                    "Ambiguous routes share the same path shape and methods: "
                    f"{existing.path!r}, {route.path!r}, {overlapping!r}."
                )
        self._routes.append(route)
        if route.name is not None:
            self._names[route.name] = route

    def get(self, name: str) -> Route:
        try:
            return self._names[name]
        except KeyError as error:
            raise RouteNotFoundError(name) from error

    def include(
        self,
        group: RouteGroup,
        *,
        prefix: str = "",
        name_prefix: str = "",
    ) -> tuple[Route, ...]:
        if not isinstance(group, RouteGroup):
            raise TypeError("Router can only include RouteGroup instances.")
        if not isinstance(name_prefix, str):
            raise TypeError("Included route name prefix must be a string.")
        added: list[Route] = []
        for definition in group.routes:
            name = (
                f"{name_prefix}{group.name_prefix}{definition.name}"
                if definition.name is not None
                else None
            )
            added.append(
                self.add(
                    join_paths(prefix, group.prefix, definition.path),
                    definition.handler,
                    methods=definition.methods,
                    name=name,
                )
            )
        return tuple(added)

    def url_path_for(self, name: str, **parameters: object) -> str:
        try:
            route = self.get(name)
        except RouteNotFoundError as error:
            raise ReverseRouteError(f"Unknown route name: {name!r}.") from error
        return route.build_path(parameters)

    def handler(self):
        from .http import RoutingHandler

        return RoutingHandler(self)

    def allowed_methods(self, path: str) -> tuple[str, ...]:
        allowed = {
            method
            for route in self._path_candidates(path)
            for method in route.methods
        }
        return tuple(sorted(allowed))

    def match(self, path: str, method: str) -> RouteMatch | None:
        normalized = self._normalize_method(method)
        candidates = [
            route
            for route in self._path_candidates(path)
            if normalized in route.methods
        ]
        if not candidates:
            return None
        selected = max(
            candidates,
            key=lambda route: (
                route.precedence,
                len(route.precedence),
                route.path,
                route.name or "",
            ),
        )
        parameters = selected.path_parameters(path)
        if parameters is None:  # pragma: no cover - guarded by candidate selection
            return None
        return RouteMatch(selected, normalized, parameters)

    def resolve(self, path: str, method: str) -> RouteMatch:
        normalized = self._normalize_method(method)
        path_candidates = self._path_candidates(path)
        if not path_candidates:
            raise RouteNotFoundError(path)
        match = self.match(path, normalized)
        if match is None:
            raise MethodNotAllowedError(
                path,
                normalized,
                tuple(
                    sorted(
                        {
                            allowed
                            for route in path_candidates
                            for allowed in route.methods
                        }
                    )
                ),
            )
        return match

    def _path_candidates(self, path: str) -> list[Route]:
        return [
            route for route in self._routes if route.path_parameters(path) is not None
        ]

    @staticmethod
    def _normalize_method(method: str) -> str:
        if not isinstance(method, str) or not _METHOD.fullmatch(method.strip()):
            raise InvalidRouteError("Request method is invalid.")
        return method.strip().upper()
