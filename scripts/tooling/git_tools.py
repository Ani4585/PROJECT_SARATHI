"""
PROJECT SARATHI

Git Repository Utilities

Provides structured Git repository information for
project status and release verification.
"""

from __future__ import annotations

from dataclasses import dataclass

from .verification import (
    run_command,
)


@dataclass(frozen=True, slots=True)
class GitStatus:
    """
    Structured Git working-tree status.
    """

    available: bool
    branch: str | None
    modified_files: tuple[str, ...]
    added_files: tuple[str, ...]
    deleted_files: tuple[str, ...]
    renamed_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    ahead: int
    behind: int

    @property
    def dirty(
        self,
    ) -> bool:
        """
        Return whether the working tree contains changes.
        """

        return any(
            (
                self.modified_files,
                self.added_files,
                self.deleted_files,
                self.renamed_files,
                self.untracked_files,
            )
        )

    @property
    def changed_file_count(
        self,
    ) -> int:
        """
        Return the total changed-file count.
        """

        return sum(
            len(files)
            for files in (
                self.modified_files,
                self.added_files,
                self.deleted_files,
                self.renamed_files,
                self.untracked_files,
            )
        )


def git_available() -> bool:
    """
    Return whether Git is available and the directory is a repository.
    """

    result = run_command(
        [
            "git",
            "rev-parse",
            "--is-inside-work-tree",
        ],
        capture_output=True,
    )

    return (
        result.passed
        and result.standard_output.strip()
        == "true"
    )


def get_current_branch() -> str | None:
    """
    Return the current Git branch.
    """

    result = run_command(
        [
            "git",
            "branch",
            "--show-current",
        ],
        capture_output=True,
    )

    if not result.passed:
        return None

    branch = result.standard_output.strip()

    return branch or None


def get_ahead_behind() -> tuple[int, int]:
    """
    Return ahead and behind counts against the upstream branch.
    """

    result = run_command(
        [
            "git",
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
        ],
        capture_output=True,
    )

    if not result.passed:
        return 0, 0

    parts = result.standard_output.strip().split()

    if len(parts) != 2:
        return 0, 0

    try:
        ahead = int(
            parts[0]
        )

        behind = int(
            parts[1]
        )

    except ValueError:
        return 0, 0

    return ahead, behind


def collect_git_status() -> GitStatus:
    """
    Collect structured Git repository status.
    """

    if not git_available():

        return GitStatus(
            available=False,
            branch=None,
            modified_files=(),
            added_files=(),
            deleted_files=(),
            renamed_files=(),
            untracked_files=(),
            ahead=0,
            behind=0,
        )

    status_result = run_command(
        [
            "git",
            "status",
            "--porcelain",
        ],
        capture_output=True,
    )

    modified: list[str] = []
    added: list[str] = []
    deleted: list[str] = []
    renamed: list[str] = []
    untracked: list[str] = []

    if status_result.passed:

        for line in status_result.standard_output.splitlines():

            if not line:
                continue

            status_code = line[:2]
            path = line[3:].strip()

            if status_code == "??":
                untracked.append(
                    path
                )
                continue

            if "R" in status_code:
                renamed.append(
                    path
                )
                continue

            if "D" in status_code:
                deleted.append(
                    path
                )
                continue

            if "A" in status_code:
                added.append(
                    path
                )
                continue

            if "M" in status_code:
                modified.append(
                    path
                )

    ahead, behind = get_ahead_behind()

    return GitStatus(
        available=True,
        branch=get_current_branch(),
        modified_files=tuple(
            modified
        ),
        added_files=tuple(
            added
        ),
        deleted_files=tuple(
            deleted
        ),
        renamed_files=tuple(
            renamed
        ),
        untracked_files=tuple(
            untracked
        ),
        ahead=ahead,
        behind=behind,
    )