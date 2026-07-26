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

        Strategy:

        1. Prefer type-based resolution.
        2. Fall back to name-based resolution.
        """

        dependencies = []

        try:

            dependency_types = (
                ConstructorInspector
                .get_dependency_types(cls)
            )

            for dependency_type in dependency_types:

                dependencies.append(
                    self._container.resolve_type(
                        dependency_type
                    )
                )


        except TypeError:

            dependency_names = (
                ConstructorInspector
                .get_dependencies(cls)
            )

            for name in dependency_names:

                dependencies.append(
                    self._container.resolve(name)
                )


        return cls(
            *dependencies
        )