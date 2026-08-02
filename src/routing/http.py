"""HTTP request dispatch adapter for the routing engine."""

from __future__ import annotations

import inspect

from src.http import Request, TextResponse

from .exceptions import MethodNotAllowedError, RouteNotFoundError
from .router import Router


class RoutingHandler:
    """Resolve requests and invoke route handlers with typed parameters."""

    def __init__(self, router: Router) -> None:
        if not isinstance(router, Router):
            raise TypeError("Routing handler requires a Router.")
        self.router = router

    async def __call__(self, request: Request) -> object:
        try:
            matched = self.router.resolve(request.path, request.method)
        except RouteNotFoundError:
            return TextResponse("Not Found", status=404)
        except MethodNotAllowedError as error:
            return TextResponse(
                "Method Not Allowed",
                status=405,
                headers=(("allow", ", ".join(error.allowed_methods)),),
            )
        result = matched.route.handler(request, **matched.parameters)
        if inspect.isawaitable(result):
            result = await result
        return result
