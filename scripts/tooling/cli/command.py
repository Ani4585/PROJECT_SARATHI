"""
PROJECT SARATHI

Developer CLI Command Contract

Defines the stable interface implemented by every developer
command registered with the PROJECT SARATHI CLI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace

from .context import CommandContext


class Command(ABC):
    """Define the contract for a PROJECT SARATHI CLI command."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique command name.

        Returns:
            The command name used on the command line.
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """Return the command description.

        Returns:
            A concise description displayed in CLI help.
        """

    def configure_parser(
        self,
        parser: ArgumentParser,
    ) -> None:
        """Configure command-specific parser options.

        Commands without custom arguments may retain this default
        implementation.

        Args:
            parser: The argument parser assigned to the command.
        """

        del parser

    @abstractmethod
    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Execute the command.

        Args:
            context: Shared CLI execution dependencies.
            arguments: Arguments parsed for this command.

        Returns:
            The process exit code produced by the command.
        """
