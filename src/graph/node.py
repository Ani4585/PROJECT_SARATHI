"""
PROJECT SARATHI

Dependency Graph Node
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DependencyNode:
    """
    Represents one node inside the
    dependency graph.
    """

    service_type: type

    implementation_type: type

    dependencies: list["DependencyNode"] = field(
        default_factory=list
    )

    def add_dependency(
        self,
        node: "DependencyNode",
    ) -> None:

        if node not in self.dependencies:
            self.dependencies.append(node)

    @property
    def name(self) -> str:

        return self.service_type.__name__

    def __repr__(self):

        return (
            f"DependencyNode({self.name})"
        )