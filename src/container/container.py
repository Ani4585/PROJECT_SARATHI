"""
PROJECT SARATHI

Dependency Injection Container.
"""

from __future__ import annotations

from threading import RLock
from typing import Any

from .dependency_tree_builder import DependencyTreeBuilder
from .descriptor import ServiceDescriptor
from .lifetimes import ServiceLifetime
from .provider import FactoryProvider
from .registry import ServiceRegistry

from src.graph import GraphRecorder
from src.reflection import ConstructorInspector
from .validator import DependencyValidator

class ServiceContainer:
    """
    Central dependency injection container.
    """

    def __init__(self) -> None:

        self._registry = ServiceRegistry()

        # Type-based dependency registrations
        self._typed_services: dict[type, Any] = {}

        # Metadata describing registered services
        self._service_descriptors: dict[
            type,
            ServiceDescriptor,
        ] = {}

        self._lock = RLock()

        # Dependency graph infrastructure
        self._graph_recorder = GraphRecorder()

        self._dependency_tree_builder = (
            DependencyTreeBuilder(
                self._graph_recorder.graph,
                ConstructorInspector(),
            )
        )
        self._validator = DependencyValidator(
            self._graph_recorder.graph
        )
        
        # Lazy-created resolver
        self._resolver = None

    # --------------------------------------------------
    # Registration
    # --------------------------------------------------

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

        Maintains backward compatibility while
        creating a ServiceDescriptor.
        """

        self._typed_services[
            service_type
        ] = instance

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=type(instance),
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
        )

        self._service_descriptors[
            service_type
        ] = descriptor

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

    # --------------------------------------------------
    # Descriptor API
    # --------------------------------------------------

    def get_descriptor(
        self,
        service_type: type,
    ) -> ServiceDescriptor | None:
        """
        Return the descriptor for a service.
        """

        return self._service_descriptors.get(
            service_type
        )

    def cache_constructor_dependencies(
        self,
        service_type: type,
        dependencies: list[type],
    ) -> None:
        """
        Cache constructor dependency metadata.
        """

        descriptor = self.get_descriptor(
        service_type
    )

        if descriptor is None:
            return

        descriptor.constructor_dependencies = list(
            dependencies
        )

        descriptor.constructor_cached = True
    # --------------------------------------------------
    # Resolution
    # --------------------------------------------------

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

    def is_registered_type(
        self,
        service_type: type,
    ) -> bool:
        """
        Check whether a service type has
        already been registered.
        """

        return (
            service_type
            in self._typed_services
        )

    # --------------------------------------------------
    # Object Construction
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Queries
    # --------------------------------------------------

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
        Check if a type registration exists.
        """

        return (
            service_type
            in self._typed_services
        )

    @property
    def graph_recorder(
        self,
    ) -> GraphRecorder:
        """
        Return the graph recorder owned
        by this container.
        """

        return self._graph_recorder

    def list_services(
        self,
    ):

        return (
            self._registry
            .list_services()
        )