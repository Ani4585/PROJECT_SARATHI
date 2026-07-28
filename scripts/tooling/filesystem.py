"""
PROJECT SARATHI

Developer Tooling Filesystem Utilities

Provides repository-root discovery, file searching,
file counting, exclusions, and required-file checks.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]


EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        "htmlcov",
        "build",
        "dist",
    }
)


def setup_project_root() -> Path:
    """
    Add the repository root to Python's import path.
    """

    root = str(
        PROJECT_ROOT
    )

    if root not in sys.path:
        sys.path.insert(
            0,
            root,
        )

    return PROJECT_ROOT


def is_excluded(
    path: Path,
) -> bool:
    """
    Determine whether a path belongs to an excluded directory.
    """

    return any(
        part in EXCLUDED_DIRECTORIES
        for part in path.parts
    )


def iter_files(
    directory: Path,
    pattern: str = "*",
) -> Iterator[Path]:
    """
    Yield matching repository files while respecting exclusions.
    """

    if not directory.exists():
        return

    for path in directory.rglob(
        pattern
    ):

        if not path.is_file():
            continue

        if is_excluded(
            path
        ):
            continue

        yield path


def count_files(
    directory: Path,
    pattern: str = "*",
) -> int:
    """
    Count matching files under a directory.
    """

    return sum(
        1
        for _ in iter_files(
            directory,
            pattern,
        )
    )


def file_exists(
    relative_path: str | Path,
) -> bool:
    """
    Check whether a repository-relative file exists.
    """

    path = (
        PROJECT_ROOT
        / relative_path
    )

    return (
        path.exists()
        and path.is_file()
    )


def directory_exists(
    relative_path: str | Path,
) -> bool:
    """
    Check whether a repository-relative directory exists.
    """

    path = (
        PROJECT_ROOT
        / relative_path
    )

    return (
        path.exists()
        and path.is_dir()
    )


def required_file_status(
    required_files: tuple[str, ...],
) -> dict[str, bool]:
    """
    Return existence results for required repository files.
    """

    return {
        relative_path: file_exists(
            relative_path
        )
        for relative_path
        in required_files
    }