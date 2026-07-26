"""
PROJECT SARATHI

Dependency Injection Container.
"""

from __future__ import annotations

from threading import RLock
from typing import Any

from .lifetimes import ServiceLifetime
from .provider import FactoryProvider
from .registry import ServiceRegistry


class ServiceContainer:
    """
    Central dependency injection container.
    """


    def __init__(self) -> None:

        self._registry = ServiceRegistry()

        # Type based dependency registrations
        self._typed_services: dict[type, Any] = {}

        self._lock = RLock()

        self._resolver = None



    def register_instance(
        self,
        name: str,
        instance: Any,
    ) -> None:
        """
        Register an already-created singleton instance.
        """

        self._registry.register(
            name=name,
            provider=lambda: instance,
            lifetime=ServiceLifetime.SINGLETON,
        )


        definition = (
            self._registry
            .get_definition(name)
        )


        definition.instance = instance



    def register_type(
        self,
        service_type: type,
        instance: Any,
    ) -> None:
        """
        Register a service by type.

        Example:

            Logger -> logger instance
            Settings -> settings instance

        Enables type based injection.
        """

        self._typed_services[
            service_type
        ] = instance



    def register_factory(
        self,
        name: str,
        factory,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """
        Register a factory function.
        """

        provider = FactoryProvider(factory)


        self._registry.register(
            name=name,
            provider=provider,
            lifetime=lifetime,
        )



    def resolve(
        self,
        name: str,
    ) -> Any:
        """
        Resolve a service by name.
        """

        definition = (
            self._registry
            .get_definition(name)
        )


        if (
            definition.lifetime
            == ServiceLifetime.SINGLETON
        ):

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

            return (
                definition.provider.create()
            )


        return definition.provider()



    def resolve_type(
        self,
        service_type: type,
    ) -> Any:
        """
        Resolve a service using its type.
        """

        if service_type not in self._typed_services:

            raise KeyError(
                f"Service type "
                f"{service_type.__name__} "
                "is not registered."
            )


        return self._typed_services[
            service_type
        ]



    def build(
        self,
        cls: type,
    ) -> Any:
        """
        Build an object using dependency injection.
        """

        if self._resolver is None:

            from .resolver import DependencyResolver

            self._resolver = DependencyResolver(
                self
            )


        return self._resolver.build(
            cls
        )



    def has(
        self,
        name: str,
    ) -> bool:

        return (
            self._registry
            .is_registered(name)
        )



    def has_type(
        self,
        service_type: type,
    ) -> bool:
        """
        Check if type registration exists.
        """

        return (
            service_type
            in self._typed_services
        )



    def list_services(self):

        return (
            self._registry
            .list_services()
        )