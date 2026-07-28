"""
PROJECT SARATHI

Developer CLI Script Command

Provides a reusable CLI command that executes a Python developer
script relative to the repository root.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from scripts.tooling.console import (
    print_error,
    print_header,
)
from scripts.tooling.verification import run_command

from ..command import Command
from ..context import CommandContext


class ScriptCommand(Command):
    """Execute a repository developer script as a CLI command."""

    def __init__(
        self,
        name: str,
        description: str,
        script_path: str | Path,
    ) -> None:
        """Initialize a script-backed command.

        Args:
            name: Command name exposed by the CLI.
            description: Description displayed in command help.
            script_path: Repository-relative path to the Python script.
        """

        self._name = name
        self._description = description
        self._script_path = Path(script_path)

    @property
    def name(self) -> str:
        """Return the command name.

        Returns:
            The registered command name.
        """

        return self._name

    @property
    def description(self) -> str:
        """Return the command description.

        Returns:
            The command help description.
        """

        return self._description

    @property
    def script_path(self) -> Path:
        """Return the configured repository-relative script path.

        Returns:
            The path of the developer script.
        """

        return self._script_path

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Execute the configured developer script.

        Args:
            context: Shared CLI execution dependencies.
            arguments: Arguments parsed for this command.

        Returns:
            The developer script exit code, or one when the script
            does not exist.
        """

        del arguments

        print_header(
            f"CLI - {self.name.upper()}"
        )

        resolved_script = (
            context.project_root
            / self.script_path
        )

        if not resolved_script.is_file():
            print_error(
                "Developer script not found: "
                f"{self.script_path}"
            )

            return 1

        result = run_command(
            [
                context.python_executable,
                str(resolved_script),
            ],
            cwd=context.project_root,
        )

        return result.return_code
