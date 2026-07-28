"""
PROJECT SARATHI

Dependency Validation Engine.

Performs static validation of dependency
graphs before object construction.
"""

from __future__ import annotations

from src.graph import CycleDetector, DependencyGraph


class DependencyValidator:
    """
    Validates dependency graphs.
    """

    def __init__(
        self,
        graph: DependencyGraph,
    ) -> None:

        self._graph = graph

    def validate(self) -> None:
        """
        Execute all validation rules.
        """

        detector = CycleDetector(
            self._graph
        )

        detector.validate()

    def has_cycles(
        self,
    ) -> bool:

        try:

            self.validate()

            return False

        except Exception:

            return True