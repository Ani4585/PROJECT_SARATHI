"""
PROJECT SARATHI

Developer CLI Execution Context

Provides explicit environmental dependencies shared by
PROJECT SARATHI developer commands.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.tooling.filesystem import PROJECT_ROOT


@dataclass(frozen=True, slots=True)
class CommandContext:
    """Store stable dependencies required during command execution.

    Attributes:
        project_root: Absolute path to the repository root.
        python_executable: Python interpreter used for child commands.
    """

    project_root: Path
    python_executable: str

    def __post_init__(self) -> None:
        """Validate and normalize context values.

        Raises:
            ValueError: If the Python executable is empty.
        """

        normalized_root = self.project_root.expanduser().resolve()
        normalized_executable = self.python_executable.strip()

        if not normalized_executable:
            raise ValueError(
                "The Python executable must not be empty."
            )

        object.__setattr__(
            self,
            "project_root",
            normalized_root,
        )
        object.__setattr__(
            self,
            "python_executable",
            normalized_executable,
        )

    @classmethod
    def create_default(cls) -> CommandContext:
        """Create the standard repository CLI context.

        Returns:
            A context using the repository root and active interpreter.
        """

        return cls(
            project_root=PROJECT_ROOT,
            python_executable=sys.executable,
        )
