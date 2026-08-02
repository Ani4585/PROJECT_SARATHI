"""
PROJECT SARATHI

Service Registry
"""

from dataclasses import dataclass
from typing import Any

from .lifetimes import ServiceLifetime

@dataclass(slots=True)
class ServiceDefinition:
    """
    Metadata describing a registered service.
    """

    name: str
    provider: Any
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    instance: Any = None


class ServiceRegistry:
    """
    Stores service definitions.
    """

    def __init__(self):
        self._services: dict[str, ServiceDefinition] = {}

    def register(
        self,
        name: str,
        provider: Any,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ):

        from .exceptions import (
            ServiceAlreadyRegisteredError,
        )

        if name in self._services:
            raise ServiceAlreadyRegisteredError(name)

        self._services[name] = ServiceDefinition(
            name=name,
            provider=provider,
            lifetime=lifetime,
        )

    def get_definition(
        self,
        name: str,
    ):

        from .exceptions import (
            ServiceNotFoundError,
        )

        if name not in self._services:
            raise ServiceNotFoundError(name)

        return self._services[name]

    def is_registered(
        self,
        name: str,
    ) -> bool:

        return name in self._services

    def unregister(self, name: str) -> ServiceDefinition:
        """Remove and return one service definition."""

        from .exceptions import ServiceNotFoundError

        try:
            return self._services.pop(name)
        except KeyError as error:
            raise ServiceNotFoundError(name) from error

    def list_services(self):

        return sorted(self._services.keys())
