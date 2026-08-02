"""Runnable M30 transaction and repository example."""

from __future__ import annotations

from dataclasses import dataclass

from src.persistence import create_persistence_runtime


@dataclass(slots=True)
class Project:
    identifier: str
    name: str


def main() -> None:
    with create_persistence_runtime(
        {"persistence.database_name": "project-sarathi-example"}
    ) as runtime:
        with runtime.unit_of_work() as work:
            projects = work.repository("projects", lambda project: project.identifier)
            projects.add(Project("sarathi", "PROJECT SARATHI"))

        with runtime.unit_of_work() as work:
            projects = work.repository("projects", lambda project: project.identifier)
            saved = projects.require("sarathi")
            print(f"Committed: {saved.identifier} | {saved.name}")

        try:
            with runtime.unit_of_work() as work:
                projects = work.repository("projects", lambda project: project.identifier)
                projects.add(Project("temporary", "Rolled Back"))
                raise RuntimeError("demonstrate rollback")
        except RuntimeError:
            pass

        with runtime.unit_of_work() as work:
            projects = work.repository("projects", lambda project: project.identifier)
            print(f"Rows after rollback: {len(projects)}")


if __name__ == "__main__":
    main()
