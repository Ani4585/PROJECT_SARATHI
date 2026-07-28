"""
PROJECT SARATHI

Dependency Plan

Represents a recursive dependency plan for a service.
This class does NOT create objects.
It only models the dependency hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DependencyPlan:
    """
    Represents one node in a dependency plan.
    """

    service_type: type

    children: list["DependencyPlan"] = field(
        default_factory=list
    )

    def add_child(
        self,
        child: "DependencyPlan",
    ) -> None:
        """
        Adds a child dependency.
        """

        self.children.append(child)

    @property
    def dependency_count(
        self,
    ) -> int:
        """
        Returns the number of direct dependencies.
        """

        return len(self.children)

    def walk(
        self,
    ):
        """
        Depth-first traversal.
        """

        yield self

        for child in self.children:
            yield from child.walk()

    def __str__(
        self,
    ) -> str:

        return self.service_type.__name__