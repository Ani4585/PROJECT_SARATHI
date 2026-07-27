"""
PROJECT SARATHI

Dependency Graph Tests
"""

from src.graph import (
    DependencyGraph,
)


class ServiceA:
    pass


class ServiceB:
    pass


class ServiceC:
    pass


def test_graph_creation():

    graph = DependencyGraph()

    graph.add_node(
        ServiceA,
        ServiceA,
    )

    graph.add_node(
        ServiceB,
        ServiceB,
    )

    graph.add_node(
        ServiceC,
        ServiceC,
    )

    graph.connect(
        ServiceA,
        ServiceB,
    )

    graph.connect(
        ServiceB,
        ServiceC,
    )

    assert len(graph) == 3