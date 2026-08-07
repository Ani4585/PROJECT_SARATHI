"""PROJECT SARATHI Web Dependency Injection Framework."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from src.container import RequestScope, ServiceContainer, ServiceLifetime, ScopeNotFoundError
from .context import HttpContext, RequestContext
from .request import Request


def inject_handler(handler: Callable | type, container: ServiceContainer) -> Callable:
    """Wrap a HTTP handler to automatically inject typed dependencies from the active RequestScope."""
    if inspect.isclass(handler):
        target = handler.__init__
        is_class = True
    else:
        target = handler
        is_class = False

    sig = inspect.signature(target)

    async def wrapper(request: Request) -> Any:
        scope: RequestScope | None = request.scope.get("request_scope")  # type: ignore[assignment]
        kwargs: dict[str, Any] = {}

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "request") and is_class:
                continue
            if param.annotation is Request:
                kwargs[param_name] = request
            elif param.annotation in (RequestContext, HttpContext):
                kwargs[param_name] = request.context
            elif scope is not None and param.annotation in container._service_descriptors:
                descriptor = container.get_descriptor(param.annotation)
                if descriptor and descriptor.lifetime in (ServiceLifetime.SCOPED, ServiceLifetime.REQUEST_SCOPED):
                    existing = scope.get(param.annotation)
                    if existing is None:
                        instance = container.build(descriptor.implementation_type)
                        scope.set(param.annotation, instance)
                        kwargs[param_name] = instance
                    else:
                        kwargs[param_name] = existing
                else:
                    kwargs[param_name] = container.build(param.annotation)

        if is_class:
            instance = handler(**kwargs)
            res = instance(request) if callable(instance) else instance.handle(request)
        else:
            res = handler(request, **kwargs) if "request" in sig.parameters else handler(**kwargs)

        if inspect.isawaitable(res):
            return await res
        return res

    return wrapper
