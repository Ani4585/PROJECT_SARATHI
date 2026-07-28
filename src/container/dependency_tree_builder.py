"""
dependency_tree_builder.py

Builds the complete recursive dependency graph for registered services.
"""

from __future__ import annotations

from typing import Type

from .constructor_inspector import ConstructorInspector
from .dependency_graph import DependencyGraph


class DependencyTreeBuilder:
    """
    Recursively builds dependency relationships
    between registered services.

    This component performs graph construction only.

    It never creates service instances.
    """

    def __init__(
        self,
        graph: DependencyGraph,
        inspector: ConstructorInspector,
    ) -> None:

        self._graph = graph
        self._inspector = inspector

        self._visited: set[type] = set()

    def build(self, service_type: Type) -> None:
        """
        Build the dependency tree for a service.
        """

        self._build_recursive(service_type)

    def _build_recursive(self, service_type: Type) -> None:
        """
        Recursively inspect constructor dependencies.
        """

        if service_type in self._visited:
            return

        self._visited.add(service_type)

        dependencies = self._inspector.get_dependencies(service_type)

        for dependency in dependencies:

            self._graph.add_dependency(
            service_type,
            dependency,
        )

            self._build_recursive(dependency)