"""
PROJECT SARATHI

Developer CLI Verification Command

Provides fail-fast orchestration of the standard repository
verification sequence through registered CLI commands.
"""

from __future__ import annotations

from argparse import Namespace

from scripts.tooling.console import (
    print_error,
    print_header,
)
from scripts.tooling.version import get_version_information

from ..command import Command
from ..context import CommandContext
from ..registry import CommandRegistry


VERIFICATION_SEQUENCE = (
    "stats",
    "status",
    "release",
)


class VerificationCommand(Command):
    """Execute the standard repository verification workflow."""

    def __init__(
        self,
        registry: CommandRegistry,
        sequence: tuple[str, ...] = VERIFICATION_SEQUENCE,
    ) -> None:
        """Initialize the verification command.

        Args:
            registry: Registry used to resolve verification commands.
            sequence: Ordered command names forming the workflow.

        Raises:
            ValueError: If the sequence is empty or recursively contains
                the verify command.
        """

        if not sequence:
            raise ValueError(
                "The verification sequence must not be empty."
            )

        if self.name in sequence:
            raise ValueError(
                "The verification sequence must not contain verify."
            )

        self._registry = registry
        self._sequence = tuple(sequence)

    @property
    def name(self) -> str:
        """Return the command name.

        Returns:
            The verification command name.
        """

        return "verify"

    @property
    def description(self) -> str:
        """Return the command description.

        Returns:
            The verification command help description.
        """

        return (
            "Run complete one-command repository verification."
        )

    @property
    def sequence(self) -> tuple[str, ...]:
        """Return the ordered verification sequence.

        Returns:
            An immutable tuple of command names.
        """

        return self._sequence

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Execute registered verification commands in order.

        Execution stops immediately when any command returns a
        non-zero exit code.

        Args:
            context: Shared CLI execution dependencies.
            arguments: Arguments parsed for this command.

        Returns:
            Zero when every command succeeds, otherwise the first
            failing command exit code.
        """

        del arguments

        print_header(
            "CLI - VERIFY"
        )

        for command_name in self.sequence:
            command = self._registry.get(
                command_name
            )

            exit_code = command.execute(
                context,
                Namespace(command=command_name),
            )

            if exit_code != 0:
                print_error(
                    "Verification stopped after "
                    f"{command_name!r} returned "
                    f"exit code {exit_code}."
                )

                return exit_code

        information = get_version_information()
        milestone_number = (
            information.milestone.removeprefix("M")
        )

        print()
        print(information.framework_name)
        print(
            "MILESTONE "
            f"{milestone_number} "
            "VERIFICATION COMPLETE"
        )
        print("READY FOR COMMIT")

        return 0
