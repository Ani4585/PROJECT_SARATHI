"""
PROJECT SARATHI

Automatic Dependency Tree Builder

Builds a complete recursive dependency graph
without creating service instances.
"""

from __future__ import annotations

from src.graph import DependencyGraph
from src.reflection import ConstructorInspector


class DependencyTreeBuilder:
    """
    Recursively builds typed dependency relationships.
    """

    def __init__(
        self,
        graph: DependencyGraph,
        inspector: ConstructorInspector,
    ) -> None:

        self._graph = graph
        self._inspector = inspector
        self._visited: set[type] = set()

    def build(
        self,
        service_type: type,
    ) -> None:
        """
        Build a fresh dependency tree for a root service.
        """

        self._visited.clear()

        self._build_recursive(
            service_type
        )

    def _build_recursive(
        self,
        service_type: type,
    ) -> None:
        """
        Recursively inspect typed dependencies.
        """

        if service_type in self._visited:
            return

        self._visited.add(
            service_type
        )

        self._graph.add_node(
            service_type
        )

        dependencies = (
            self._inspector
            .get_dependency_types(service_type)
        )

        for dependency_type in dependencies:

            self._graph.add_node(
                dependency_type
            )

            self._graph.add_dependency(
                service_type,
                dependency_type,
            )

            self._build_recursive(
                dependency_type
            )