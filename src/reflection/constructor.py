"""
PROJECT SARATHI

Constructor Reflection Utilities

Responsible for inspecting classes and discovering
constructor dependencies.
"""

from __future__ import annotations

import inspect


class ConstructorInspector:
    """
    Inspects constructors for dependency information.
    """

    @staticmethod
    def _parameters(
        cls: type,
    ) -> list[inspect.Parameter]:
        """
        Return injectable constructor parameters.
        """

        signature = inspect.signature(
            cls.__init__
        )

        parameters: list[inspect.Parameter] = []

        for parameter in signature.parameters.values():

            if parameter.name == "self":
                continue

            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            parameters.append(parameter)

        return parameters

    @staticmethod
    def get_dependencies(
        cls: type,
    ) -> list[str]:
        """
        Return constructor parameter names.
        """

        return [
            parameter.name
            for parameter
            in ConstructorInspector._parameters(cls)
        ]

    @staticmethod
    def get_dependency_types(
        cls: type,
    ) -> list[type]:
        """
        Return constructor parameter types.
        """

        dependency_types: list[type] = []

        for parameter in ConstructorInspector._parameters(
            cls
        ):

            if parameter.annotation is inspect.Signature.empty:

                raise TypeError(
                    f"{cls.__name__}.{parameter.name} "
                    "is missing a type annotation."
                )

            dependency_types.append(
                parameter.annotation
            )

        return dependency_types