from typing import Dict, Any
from .router import GatewayRouter

class OpenAPIGenerator:
    def __init__(self, title: str = "Sarathi Gateway API", version: str = "1.0.0", description: str = ""):
        self.title = title
        self.version = version
        self.description = description

    def generate(self, router: GatewayRouter) -> Dict[str, Any]:
        paths: Dict[str, Dict[str, Any]] = {}

        for route in router.routes:
            path_key = route.path_pattern
            if path_key not in paths:
                paths[path_key] = {}

            for method in route.methods:
                if method == "*":
                    continue
                method_key = method.lower()
                parameters = []
                for p in route._param_names:
                    parameters.append({
                        "name": p,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    })

                paths[path_key][method_key] = {
                    "summary": route.name,
                    "operationId": f"{method_key}_{route.name}",
                    "parameters": parameters,
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }

        return {
            "openapi": "3.1.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description
            },
            "paths": paths
        }
