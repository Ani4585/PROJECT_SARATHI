"""Routing boundary exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class RoutingError(SarathiException):
    def __init__(
        self,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, error_code="ROUTING_ERROR", details=details)


class InvalidRouteError(RoutingError):
    pass


class UnknownConverterError(RoutingError):
    pass


class ParameterConversionError(RoutingError):
    pass


class RouteConflictError(RoutingError):
    pass


class ReverseRouteError(RoutingError):
    pass


class RouteNotFoundError(RoutingError):
    status_code = 404

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"No route matches path {path!r}.", details={"path": path})


class MethodNotAllowedError(RoutingError):
    status_code = 405

    def __init__(self, path: str, method: str, allowed_methods: tuple[str, ...]) -> None:
        self.path = path
        self.method = method
        self.allowed_methods = allowed_methods
        super().__init__(
            f"Method {method!r} is not allowed for path {path!r}.",
            details={
                "path": path,
                "method": method,
                "allowed_methods": allowed_methods,
            },
        )
