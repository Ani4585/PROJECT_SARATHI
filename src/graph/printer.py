"""
PROJECT SARATHI

Dependency Graph Printer

Formats a dependency graph into a
human-readable tree.
"""

from __future__ import annotations

from .graph import DependencyGraph
from .node import DependencyNode


class GraphPrinter:
    """
    Prints a dependency graph.
    """

    def __init__(
        self,
        graph: DependencyGraph,
    ) -> None:

        self._graph = graph

    def print(self) -> str:
        """
        Return a formatted graph.
        """

        if len(self._graph) == 0:
            return "Dependency graph is empty."

        lines: list[str] = []

        visited: set[type] = set()

        for node in self._graph:

            if node.service_type in visited:
                continue

            self._print_node(
                node,
                lines,
                visited,
                "",
            )

        return "\n".join(lines)

    def _print_node(
        self,
        node: DependencyNode,
        lines: list[str],
        visited: set[type],
        prefix: str,
    ) -> None:

        visited.add(
            node.service_type
        )

        lines.append(
            f"{prefix}{node.name}"
        )

        for dependency in node.dependencies:

            self._print_node(
                dependency,
                lines,
                visited,
                prefix + "    ",
            )