"""
PROJECT SARATHI

Dependency Graph Traversal

Provides graph traversal algorithms for
dependency analysis.
"""

from __future__ import annotations

from collections.abc import Iterator

from .graph import DependencyGraph
from .node import DependencyNode


class GraphTraversal:
    """
    Traverses a dependency graph.

    Initially this class provides a
    Depth-First Search (DFS) traversal.

    Future versions will support:

    - Breadth-First Search (BFS)
    - Topological Ordering
    - Startup Ordering
    - Dependency Reports
    """

    def __init__(
        self,
        graph: DependencyGraph,
    ) -> None:

        self._graph = graph

    def depth_first(
        self,
        root: DependencyNode,
    ) -> Iterator[DependencyNode]:
        """
        Perform a depth-first traversal
        starting from the given node.
        """

        visited: set[type] = set()

        yield from self._dfs(
            root,
            visited,
        )

    def _dfs(
        self,
        node: DependencyNode,
        visited: set[type],
    ) -> Iterator[DependencyNode]:
        """
        Recursive DFS implementation.
        """

        if node.service_type in visited:
            return

        visited.add(
            node.service_type
        )

        yield node

        for dependency in node.dependencies:

            yield from self._dfs(
                dependency,
                visited,
            )