"""
PROJECT SARATHI

Developer CLI Command Registry

Provides explicit, deterministic registration and resolution
of PROJECT SARATHI developer commands.
"""

from __future__ import annotations

from collections.abc import Iterator

from .command import Command


class CommandRegistryError(Exception):
    """Base exception for command registry failures."""


class CommandAlreadyRegisteredError(CommandRegistryError):
    """Raised when a command name is registered more than once."""


class CommandNotFoundError(CommandRegistryError):
    """Raised when a requested command is not registered."""


class CommandRegistry:
    """Register and resolve CLI commands by unique name."""

    def __init__(self) -> None:
        """Initialize an empty command registry."""

        self._commands: dict[str, Command] = {}

    def register(
        self,
        command: Command,
    ) -> None:
        """Register one command.

        Args:
            command: Command instance to register.

        Raises:
            ValueError: If the command name is empty or contains
                surrounding whitespace.
            CommandAlreadyRegisteredError: If another command already
                uses the same name.
        """

        command_name = command.name

        if not command_name:
            raise ValueError(
                "Command names must not be empty."
            )

        if command_name != command_name.strip():
            raise ValueError(
                "Command names must not contain surrounding whitespace."
            )

        if command_name in self._commands:
            raise CommandAlreadyRegisteredError(
                f"Command already registered: {command_name}"
            )

        self._commands[command_name] = command

    def get(
        self,
        name: str,
    ) -> Command:
        """Resolve a registered command.

        Args:
            name: Command name to resolve.

        Returns:
            The registered command.

        Raises:
            CommandNotFoundError: If the command is not registered.
        """

        try:
            return self._commands[name]
        except KeyError as error:
            raise CommandNotFoundError(
                f"Command not registered: {name}"
            ) from error

    def unregister(self, name: str) -> Command:
        """Remove and return one command registration."""

        try:
            return self._commands.pop(name)
        except KeyError as error:
            raise CommandNotFoundError(
                f"Command not registered: {name}"
            ) from error

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether a command is registered.

        Args:
            name: Command name to inspect.

        Returns:
            True when the command is registered.
        """

        return name in self._commands

    def commands(self) -> tuple[Command, ...]:
        """Return registered commands in deterministic name order.

        Returns:
            An immutable tuple of registered commands.
        """

        return tuple(
            self._commands[name]
            for name in sorted(self._commands)
        )

    def names(self) -> tuple[str, ...]:
        """Return registered command names in deterministic order.

        Returns:
            An immutable tuple of command names.
        """

        return tuple(
            sorted(self._commands)
        )

    def __len__(self) -> int:
        """Return the number of registered commands."""

        return len(self._commands)

    def __iter__(self) -> Iterator[Command]:
        """Iterate over commands in deterministic order."""

        return iter(self.commands())
