"""PROJECT SARATHI OpenAPI 3.0 Specification Generator."""

from __future__ import annotations

import inspect
from typing import Any


class OpenApiGenerator:
    """Generates OpenAPI 3.0.3 specification from REST controllers."""

    def __init__(self, title: str = "PROJECT SARATHI API", version: str = "1.0.0") -> None:
        self.title = title
        self.version = version
        self._controllers: list[type] = []

    def register_controller(self, controller_cls: type) -> None:
        if controller_cls not in self._controllers:
            self._controllers.append(controller_cls)

    def generate_schema(self) -> dict[str, Any]:
        paths: dict[str, Any] = {}

        for controller_cls in self._controllers:
            prefix = getattr(controller_cls, "__controller_prefix__", "")
            for _, method in inspect.getmembers(controller_cls, predicate=inspect.isfunction):
                route_method = getattr(method, "__route_method__", None)
                route_path = getattr(method, "__route_path__", None)

                if route_method and route_path is not None:
                    full_path = f"{prefix}{route_path}".rstrip("/") or "/"
                    if full_path not in paths:
                        paths[full_path] = {}

                    sig = inspect.signature(method)
                    params_spec: list[dict[str, Any]] = []

                    for name, param in sig.parameters.items():
                        if name in ("self", "req", "request"):
                            continue
                        in_location = "path" if f"{{{name}}}" in full_path else "query"
                        params_spec.append({
                            "name": name,
                            "in": in_location,
                            "required": in_location == "path" or param.default == inspect.Parameter.empty,
                            "schema": {"type": "string"},
                        })

                    paths[full_path][route_method.lower()] = {
                        "summary": method.__name__.replace("_", " ").title(),
                        "parameters": params_spec,
                        "responses": {
                            "200": {"description": "Successful operation"},
                            "400": {"description": "Bad Request / Problem Details"},
                        },
                    }

        return {
            "openapi": "3.0.3",
            "info": {"title": self.title, "version": self.version},
            "paths": paths,
        }
