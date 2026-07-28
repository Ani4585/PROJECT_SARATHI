"""
PROJECT SARATHI

Dependency Graph Recorder

Records dependency relationships while
objects are being resolved.
"""

from __future__ import annotations

from .graph import DependencyGraph


class GraphRecorder:

    def __init__(self):

        self._graph = DependencyGraph()

        self._stack: list[type] = []

    @property
    def graph(self) -> DependencyGraph:

        return self._graph

    def begin(
        self,
        service_type: type,
    ) -> None:

        self._graph.add_node(
            service_type,
            service_type,
        )

        if self._stack:

            parent = self._stack[-1]

            self._graph.add_node(
                parent,
                parent,
            )

            self._graph.connect(
                parent,
                service_type,
            )

        self._stack.append(
            service_type
        )

    def end(self) -> None:

        if self._stack:

            self._stack.pop()
            
    def record(
        self,
        parent: type,
        child: type,
    ) -> None:
        """
        Record a dependency relationship without
        using the runtime resolution stack.

        Used by DependencyPlanner.
        """

        self._graph.add_node(
            parent,
            parent,
        )

        self._graph.add_node(
            child,
            child,
        )

        self._graph.connect(
            parent,
            child,
        )

    def reset(self) -> None:

        self._stack.clear()

        self._graph.clear()