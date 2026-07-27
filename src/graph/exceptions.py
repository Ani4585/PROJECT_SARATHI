"""
PROJECT SARATHI

Dependency Graph Exceptions
"""


class DependencyGraphError(Exception):
    """
    Base dependency graph exception.
    """


class CircularDependencyError(DependencyGraphError):
    """
    Raised when a circular dependency
    is detected.
    """

    def __init__(
        self,
        cycle: list[type],
    ) -> None:

        self.cycle = cycle

        names = [
            cls.__name__
            for cls in cycle
        ]

        message = (
            "Circular dependency detected:\n\n"
            + " -> ".join(names)
        )

        super().__init__(message)