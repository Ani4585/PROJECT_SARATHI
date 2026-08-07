"""PROJECT SARATHI REST Controller Router."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from src.http import InvalidMessageError, Request, Response
from .binding import FromBody, FromHeader, FromPath, FromQuery, FromServices
from .exceptions import ProblemDetails, RestValidationError
from .negotiation import ContentNegotiator


class RestControllerRouter:
    """Dispatches HTTP requests to REST Controllers with automatic parameter binding."""

    def __init__(self, container: Any = None) -> None:
        self.container = container
        self._routes: list[tuple[str, str, type, Callable]] = []

    def register(self, controller_cls: type) -> None:
        prefix = getattr(controller_cls, "__controller_prefix__", "")
        for _, method in inspect.getmembers(controller_cls, predicate=inspect.isfunction):
            route_method = getattr(method, "__route_method__", None)
            route_path = getattr(method, "__route_path__", None)
            if route_method and route_path is not None:
                full_path = f"{prefix}{route_path}".rstrip("/") or "/"
                self._routes.append((route_method, full_path, controller_cls, method))

    async def handle_request(self, request: Request, controller_instance: Any, method: Callable) -> Response:
        sig = inspect.signature(method)
        kwargs: dict[str, Any] = {}
        errors: dict[str, list[str]] = {}

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if param.annotation is Request or name == "request":
                kwargs[name] = request
                continue

            default_val = param.default if param.default != inspect.Parameter.empty else None

            # Path params
            if f"{{{name}}}" in request.path or name in request.path_params:
                val = request.path_params.get(name)
                if val is not None:
                    kwargs[name] = val
                else:
                    errors[name] = [f"Path parameter '{name}' is required."]
                continue

            # Query params
            query_val = request.query_param(name)
            if query_val is not None:
                kwargs[name] = query_val
            elif default_val is not None:
                kwargs[name] = default_val
            elif "body" in name.lower() or name == "payload":
                try:
                    kwargs[name] = await request.json()
                except InvalidMessageError as err:
                    errors["body"] = [str(err)]
            elif param.default == inspect.Parameter.empty:
                errors[name] = [f"Missing required parameter '{name}'."]

        if errors:
            problem = ProblemDetails(
                title="Bad Request",
                status=400,
                detail="One or more validation errors occurred.",
                errors=errors,
            )
            return ContentNegotiator.serialize(problem)

        try:
            if inspect.ismethod(method):
                result = method(**kwargs)
            else:
                result = method(controller_instance, **kwargs)

            if inspect.isawaitable(result):
                result = await result
            return ContentNegotiator.serialize(result, request.header("accept", "application/json") or "application/json")
        except RestValidationError as err:
            return ContentNegotiator.serialize(err.problem)
        except Exception as err:
            problem = ProblemDetails(
                title="Internal Server Error",
                status=500,
                detail=str(err),
            )
            return ContentNegotiator.serialize(problem)
