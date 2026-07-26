"""
PROJECT SARATHI

Dependency Injection Container.
"""

from __future__ import annotations

from threading import RLock
from typing import Any, TypeAlias
from collections.abc import Callable

ServiceKey: TypeAlias = str | type

from .lifetimes import ServiceLifetime
from .provider import FactoryProvider
from .registry import ServiceRegistry


class ServiceContainer:
    """
    Central dependency injection container.
    """

    def __init__(self) -> None:

        self._registry = ServiceRegistry()

        self._lock = RLock()

    def register_instance(
        self,
        key: ServiceKey,
        instance: Any,
    ) -> None:
        """
        Register an already-created singleton instance.
        """

        self._registry.register(
            name=str(key),
            provider=lambda: instance,
            lifetime=ServiceLifetime.SINGLETON,
        )

        definition = self._registry.get_definition(str(key))

        definition.instance = instance

    def register_factory(
        self,
        key: ServiceKey,
        factory : Callable[..., Any],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """
        Register a factory function.
        """

        provider = FactoryProvider(factory)

        self._registry.register(
            name=str(key),
            provider=provider,
            lifetime=lifetime,
        )

    def resolve(
        self,
        key: ServiceKey,
    ) -> Any:
        """
        Resolve a service.
        """

        definition = self._registry.get_definition(str(key))

        if definition.lifetime == ServiceLifetime.SINGLETON:

            with self._lock:

                if definition.instance is None:

                    if isinstance(
                        definition.provider,
                        FactoryProvider,
                    ):
                        definition.instance = (
                            definition.provider.create()
                        )
                    else:
                        definition.instance = (
                            definition.provider()
                        )

                return definition.instance

        if isinstance(
            definition.provider,
            FactoryProvider,
        ):
            return definition.provider.create()

        return definition.provider()

    def has(
        self,
        key: ServiceKey,
    ) -> bool:

        return self._registry.is_registered(str(key))

    def list_services(self)  -> list[str]:

        return self._registry.list_services()