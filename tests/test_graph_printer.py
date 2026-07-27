"""
PROJECT SARATHI

Dependency Graph Printer Tests
"""

from src.graph import (
    DependencyGraph,
    GraphPrinter,
)


class ServiceA:
    pass


class ServiceB:
    pass


class ServiceC:
    pass


def test_graph_printer():

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

    printer = GraphPrinter(
        graph
    )

    output = printer.print()

    assert "ServiceA" in output
    assert "ServiceB" in output
    assert "ServiceC" in output