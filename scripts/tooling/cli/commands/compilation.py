"""
PROJECT SARATHI

Developer CLI Compilation Command

Provides the native CLI command used to compile all maintained
PROJECT SARATHI Python source locations.
"""

from __future__ import annotations

from argparse import Namespace

from scripts.tooling.console import print_header
from scripts.tooling.verification import run_command

from ..command import Command
from ..context import CommandContext


COMPILATION_TARGETS = (
    "src",
    "config",
    "scripts",
    "tests",
    "sarathi.py",
)


class CompilationCommand(Command):
    """Compile maintained Python files for syntax verification."""

    @property
    def name(self) -> str:
        """Return the command name.

        Returns:
            The compilation command name.
        """

        return "compile"

    @property
    def description(self) -> str:
        """Return the command description.

        Returns:
            The compilation command help description.
        """

        return "Compile source, configuration, scripts, and tests."

    @property
    def targets(self) -> tuple[str, ...]:
        """Return the configured compilation targets.

        Returns:
            An immutable tuple of repository paths.
        """

        return COMPILATION_TARGETS

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Compile the repository Python files.

        Args:
            context: Shared CLI execution dependencies.
            arguments: Arguments parsed for this command.

        Returns:
            The compileall process exit code.
        """

        del arguments

        print_header(
            "CLI - COMPILE"
        )

        result = run_command(
            [
                context.python_executable,
                "-m",
                "compileall",
                *self.targets,
            ],
            cwd=context.project_root,
        )

        return result.return_code
