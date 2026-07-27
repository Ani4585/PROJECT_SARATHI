"""
PROJECT SARATHI

Dependency Graph Cycle Detector

Detects circular dependencies inside
the dependency graph.
"""

from __future__ import annotations

from .exceptions import CircularDependencyError
from .graph import DependencyGraph
from .node import DependencyNode


class CycleDetector:
    """
    Detects dependency cycles using
    depth-first search.
    """

    def __init__(
        self,
        graph: DependencyGraph,
    ) -> None:

        self._graph = graph

    def validate(self) -> None:
        """
        Validate the dependency graph.

        Raises:
            CircularDependencyError
            if a cycle is found.
        """

        visited: set[type] = set()
        active: list[type] = []

        for node in self._graph:

            self._visit(
                node,
                visited,
                active,
            )

    def _visit(
        self,
        node: DependencyNode,
        visited: set[type],
        active: list[type],
    ) -> None:

        service = node.service_type

        if service in active:

            start = active.index(service)

            cycle = (
                active[start:]
                + [service]
            )

            raise CircularDependencyError(
                cycle
            )

        if service in visited:
            return

        active.append(service)

        for dependency in node.dependencies:

            self._visit(
                dependency,
                visited,
                active,
            )

        active.pop()

        visited.add(service)