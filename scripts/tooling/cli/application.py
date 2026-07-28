"""
PROJECT SARATHI

Developer CLI Application

Builds the command-line parser and dispatches registered
developer commands through a shared execution context.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .commands.builtins import create_builtin_registry
from .context import CommandContext
from .registry import CommandRegistry


DEFAULT_PROGRAM_NAME = "sarathi"
DEFAULT_DESCRIPTION = (
    "PROJECT SARATHI developer tooling command-line interface."
)


class CliApplication:
    """Build and execute the PROJECT SARATHI developer CLI."""

    def __init__(
        self,
        registry: CommandRegistry,
        context: CommandContext,
        *,
        program_name: str = DEFAULT_PROGRAM_NAME,
        description: str = DEFAULT_DESCRIPTION,
    ) -> None:
        """Initialize the CLI application.

        Args:
            registry: Registry containing available commands.
            context: Shared command execution context.
            program_name: Name displayed in command-line help.
            description: Description displayed in command-line help.
        """

        self._registry = registry
        self._context = context
        self._program_name = program_name
        self._description = description

    def build_parser(self) -> argparse.ArgumentParser:
        """Build the complete command-line parser.

        Returns:
            The configured root argument parser.
        """

        parser = argparse.ArgumentParser(
            prog=self._program_name,
            description=self._description,
        )

        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
        )

        for command in self._registry:
            command_parser = subparsers.add_parser(
                command.name,
                help=command.description,
                description=command.description,
            )

            command.configure_parser(
                command_parser
            )

        return parser

    def run(
        self,
        arguments: Sequence[str] | None = None,
    ) -> int:
        """Parse arguments and execute the selected command.

        Args:
            arguments: Optional command-line arguments. When omitted,
                arguments are read from the active process.

        Returns:
            The exit code returned by the selected command.
        """

        parser = self.build_parser()

        parsed_arguments = parser.parse_args(
            (
                list(arguments)
                if arguments is not None
                else None
            )
        )

        selected_command = self._registry.get(
            parsed_arguments.command
        )

        return selected_command.execute(
            self._context,
            parsed_arguments,
        )


def create_cli_application(
    context: CommandContext | None = None,
) -> CliApplication:
    """Create the standard PROJECT SARATHI CLI application.

    Args:
        context: Optional execution context. When omitted, the
            repository default context is created.

    Returns:
        A CLI application containing every built-in command.
    """

    resolved_context = (
        context
        if context is not None
        else CommandContext.create_default()
    )

    return CliApplication(
        registry=create_builtin_registry(),
        context=resolved_context,
    )
