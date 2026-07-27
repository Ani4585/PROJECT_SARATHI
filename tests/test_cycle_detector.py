"""
PROJECT SARATHI

Cycle Detector Tests
"""

from src.graph import (
    CircularDependencyError,
    CycleDetector,
    DependencyGraph,
)


class ServiceA:
    pass


class ServiceB:
    pass


class ServiceC:
    pass


def test_cycle_detection():

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

    graph.connect(
        ServiceC,
        ServiceA,
    )

    detector = CycleDetector(
        graph
    )

    try:

        detector.validate()

    except CircularDependencyError:

        return

    raise AssertionError(
        "Expected CircularDependencyError."
    )