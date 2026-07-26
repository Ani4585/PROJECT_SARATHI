"""
PROJECT SARATHI

Constructor Reflection Utilities

Responsible for inspecting classes
and discovering constructor dependencies.
"""

from __future__ import annotations

import inspect


class ConstructorInspector:
    """
    Inspects constructors for dependency information.
    """

    @staticmethod
    def get_dependencies(
        cls: type,
    ) -> list[str]:
        """
        Return constructor parameter names.

        This supports the original
        name-based dependency injection.
        """

        signature = inspect.signature(
            cls.__init__
        )

        dependencies = []

        for parameter in signature.parameters.values():

            if parameter.name == "self":
                continue

            dependencies.append(
                parameter.name
            )

        return dependencies


    @staticmethod
    def get_dependency_types(
        cls: type,
    ) -> list[type]:
        """
        Return constructor parameter types.

        This supports type-based dependency injection.
        """

        signature = inspect.signature(
            cls.__init__
        )

        dependency_types = []

        for parameter in signature.parameters.values():

            if parameter.name == "self":
                continue

            if parameter.annotation is inspect._empty:
                raise TypeError(
                    f"{cls.__name__}.{parameter.name} "
                    "is missing a type annotation."
                )

            dependency_types.append(
                parameter.annotation
            )

        return dependency_types