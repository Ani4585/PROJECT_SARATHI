"""
PROJECT SARATHI

Developer CLI Version Command

Displays the authoritative PROJECT SARATHI framework metadata
through the developer command-line interface.
"""

from __future__ import annotations

from argparse import Namespace

from scripts.tooling.console import (
    print_header,
    print_key_value,
)
from scripts.tooling.version import get_version_information

from ..command import Command
from ..context import CommandContext


class VersionCommand(Command):
    """Display authoritative framework version information."""

    @property
    def name(self) -> str:
        """Return the command name.

        Returns:
            The version command name.
        """

        return "version"

    @property
    def description(self) -> str:
        """Return the command description.

        Returns:
            The version command help description.
        """

        return "Display PROJECT SARATHI version information."

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Display the current framework metadata.

        Args:
            context: Shared CLI execution dependencies.
            arguments: Arguments parsed for this command.

        Returns:
            Zero after displaying the version information.
        """

        del context
        del arguments

        information = get_version_information()

        print_header(
            "CLI - VERSION"
        )

        print_key_value(
            "Framework",
            information.framework_name,
        )

        print_key_value(
            "Version",
            information.version,
        )

        print_key_value(
            "Milestone",
            information.milestone,
        )

        print_key_value(
            "Build Date",
            information.build_date,
        )

        return 0
