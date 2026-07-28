"""
PROJECT SARATHI

Developer CLI Test Command

Provides the native CLI command used to execute the complete
PROJECT SARATHI automated test suite.
"""

from __future__ import annotations

from argparse import Namespace

from scripts.tooling.console import print_header
from scripts.tooling.verification import run_command

from ..command import Command
from ..context import CommandContext


class TestCommand(Command):
    """Execute the repository automated test suite."""

    @property
    def name(self) -> str:
        """Return the command name.

        Returns:
            The test command name.
        """

        return "test"

    @property
    def description(self) -> str:
        """Return the command description.

        Returns:
            The test command help description.
        """

        return "Run the complete pytest suite."

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Execute pytest using the active Python interpreter.

        Args:
            context: Shared CLI execution dependencies.
            arguments: Arguments parsed for this command.

        Returns:
            The pytest process exit code.
        """

        del arguments

        print_header(
            "CLI - TEST"
        )

        result = run_command(
            [
                context.python_executable,
                "-m",
                "pytest",
                "-v",
            ],
            cwd=context.project_root,
        )

        return result.return_code
