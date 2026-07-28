"""
PROJECT SARATHI

Dependency Graph
"""

from __future__ import annotations

from .node import DependencyNode


class DependencyGraph:
    """
    Stores dependency relationships.
    """

    def __init__(self) -> None:

        self._nodes: dict[
            type,
            DependencyNode,
        ] = {}

    def add_node(
        self,
        service_type: type,
        implementation_type: type | None = None,    
    ) -> DependencyNode:
        """
        Add a node to the dependency graph.

        If no implementation type is supplied,
        assume the service type is also the
        implementation type.
        """

        if implementation_type is None:
            implementation_type = service_type

        node = self._nodes.get(
        service_type
    )

        if node is None:

            node = DependencyNode(
            service_type,
            implementation_type,
        )

        self._nodes[
            service_type
        ] = node

        return node

    def get_node(
        self,
        service_type: type,
    ) -> DependencyNode | None:

        return self._nodes.get(
            service_type
        )

    def contains(
        self,
        service_type: type,
    ) -> bool:

        return (
            service_type
            in self._nodes
        )

    def connect(
        self,
        parent: type,
        child: type,
    ) -> None:

        parent_node = self._nodes[parent]
        child_node = self._nodes[child]

        parent_node.add_dependency(
            child_node
        )

    def add_dependency(
        self,
        parent: type,
        child: type,
    ) -> None:
        """
        Compatibility wrapper used by
        dependency planners.
        """

        self.connect(
        parent,
        child,
    )

    def clear(self) -> None:

        self._nodes.clear()

    def __iter__(self):

        return iter(
            self._nodes.values()
        )

    def __len__(self):

        return len(
            self._nodes
        )