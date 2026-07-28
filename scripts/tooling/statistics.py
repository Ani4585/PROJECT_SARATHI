"""
PROJECT SARATHI

Repository Statistics

Calculates reusable repository metrics for project
status, health checks, and release reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .filesystem import (
    PROJECT_ROOT,
    count_files,
    iter_files,
)


@dataclass(frozen=True, slots=True)
class RepositoryStatistics:
    """
    Immutable repository statistics snapshot.
    """

    source_files: int
    configuration_files: int
    developer_scripts: int
    automated_test_files: int
    documentation_files: int
    source_packages: int
    python_lines: int

    def as_dict(
        self,
    ) -> dict[str, int]:
        """
        Return display-friendly statistics.
        """

        return {
            "Source Files": self.source_files,
            "Configuration Files": self.configuration_files,
            "Developer Scripts": self.developer_scripts,
            "Automated Test Files": self.automated_test_files,
            "Documentation Files": self.documentation_files,
            "Source Packages": self.source_packages,
            "Python Lines": self.python_lines,
        }


def count_python_lines(
    directories: tuple[Path, ...],
) -> int:
    """
    Count physical lines across Python files.
    """

    total = 0

    for directory in directories:

        for path in iter_files(
            directory,
            "*.py",
        ):

            try:
                with path.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    total += sum(
                        1
                        for _ in file
                    )

            except UnicodeDecodeError:
                with path.open(
                    "r",
                    encoding="utf-8-sig",
                ) as file:
                    total += sum(
                        1
                        for _ in file
                    )

    return total


def collect_repository_statistics(
    root: Path = PROJECT_ROOT,
) -> RepositoryStatistics:
    """
    Collect current repository statistics.
    """

    source_directory = (
        root
        / "src"
    )

    configuration_directory = (
        root
        / "config"
    )

    scripts_directory = (
        root
        / "scripts"
    )

    tests_directory = (
        root
        / "tests"
    )

    documentation_directory = (
        root
        / "docs"
    )

    python_directories = (
        source_directory,
        configuration_directory,
        scripts_directory,
        tests_directory,
    )

    return RepositoryStatistics(
        source_files=count_files(
            source_directory,
            "*.py",
        ),
        configuration_files=count_files(
            configuration_directory,
            "*.py",
        ),
        developer_scripts=count_files(
            scripts_directory,
            "*.py",
        ),
        automated_test_files=count_files(
            tests_directory,
            "test_*.py",
        ),
        documentation_files=count_files(
            documentation_directory,
            "*.md",
        ),
        source_packages=count_files(
            source_directory,
            "__init__.py",
        ),
        python_lines=count_python_lines(
            python_directories
        ),
    )