"""
PROJECT SARATHI

Dependency Resolver

Responsible for constructing objects and
resolving constructor dependencies.
"""

from __future__ import annotations

from typing import Any

from src.reflection import ConstructorInspector


class DependencyResolver:
    """
    Creates objects using constructor injection.
    """

    def __init__(
        self,
        container,
    ) -> None:

        self._container = container

    def build(
        self,
        cls: type,
    ) -> Any:
        """
        Build an object using constructor injection.
        """

        descriptor = (
            self._container.get_descriptor(cls)
        )

        # -----------------------------
        # Try cached constructor metadata
        # -----------------------------

        if (
            descriptor is not None
            and descriptor.constructor_cached
        ):

            dependency_types = (
                descriptor.constructor_dependencies
            )

        else:

            try:

                dependency_types = (
                    ConstructorInspector
                    .get_dependency_types(cls)
                )

                self._container.cache_constructor_dependencies(
                    cls,
                    dependency_types,
                )

            except TypeError:

                dependency_names = (
                    ConstructorInspector
                    .get_dependencies(cls)
                )

                dependencies = []

                for name in dependency_names:

                    dependencies.append(
                        self._container.resolve(name)
                    )

                instance = cls(
                    *dependencies
                )

                if not self._container.has_type(
                    cls
                ):
                    self._container.register_type(
                        cls,
                        instance,
                    )

                return instance

        dependencies = []

        for dependency_type in dependency_types:

            if self._container.has_type(
                dependency_type
            ):

                dependency = (
                    self._container.resolve_type(
                        dependency_type
                    )
                )

            else:

                dependency = self.build(
                    dependency_type
                )

            dependencies.append(
                dependency
            )

        instance = cls(
            *dependencies
        )

        if not self._container.has_type(
            cls
        ):
            self._container.register_type(
                cls,
                instance,
            )

        descriptor = (
            self._container.get_descriptor(
                cls
            )
        )

        if descriptor is not None:

            descriptor.build_count += 1

        return instance