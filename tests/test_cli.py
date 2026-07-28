"""
Tests for the PROJECT SARATHI developer CLI foundation.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import pytest

from scripts.tooling.cli.command import Command
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.cli.registry import (
    CommandAlreadyRegisteredError,
    CommandNotFoundError,
    CommandRegistry,
)
from scripts.tooling.filesystem import PROJECT_ROOT


class ExampleCommand(Command):
    """Provide a controllable command for CLI foundation tests."""

    def __init__(
        self,
        name: str = "example",
        description: str = "Execute an example command.",
        exit_code: int = 0,
    ) -> None:
        """Initialize the example command.

        Args:
            name: Command name exposed to the registry.
            description: Command help description.
            exit_code: Exit code returned during execution.
        """

        self._name = name
        self._description = description
        self._exit_code = exit_code

    @property
    def name(self) -> str:
        """Return the example command name."""

        return self._name

    @property
    def description(self) -> str:
        """Return the example command description."""

        return self._description

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Return the configured test exit code."""

        del context
        del arguments

        return self._exit_code


def test_default_context_uses_repository_environment() -> None:
    """The default context should expose stable repository dependencies."""

    context = CommandContext.create_default()

    assert context.project_root == PROJECT_ROOT.resolve()
    assert context.python_executable == sys.executable


def test_context_normalizes_project_root(
    tmp_path: Path,
) -> None:
    """The context should normalize its repository path."""

    context = CommandContext(
        project_root=tmp_path / ".." / tmp_path.name,
        python_executable=sys.executable,
    )

    assert context.project_root == tmp_path.resolve()


def test_context_rejects_empty_python_executable(
    tmp_path: Path,
) -> None:
    """The context should reject an empty interpreter value."""

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        CommandContext(
            project_root=tmp_path,
            python_executable="   ",
        )


def test_command_default_parser_configuration() -> None:
    """A command without options should accept parser configuration."""

    command = ExampleCommand()
    parser = ArgumentParser()

    assert command.configure_parser(parser) is None


def test_registry_registers_and_resolves_command() -> None:
    """The registry should return the registered command instance."""

    registry = CommandRegistry()
    command = ExampleCommand()

    registry.register(command)

    assert registry.get("example") is command
    assert registry.contains("example") is True
    assert len(registry) == 1


def test_registry_rejects_duplicate_command_name() -> None:
    """The registry should reject duplicate command names."""

    registry = CommandRegistry()
    registry.register(ExampleCommand())

    with pytest.raises(
        CommandAlreadyRegisteredError,
        match="already registered",
    ):
        registry.register(
            ExampleCommand(exit_code=1)
        )


@pytest.mark.parametrize(
    "invalid_name",
    (
        "",
        " ",
        " example",
        "example ",
    ),
)
def test_registry_rejects_invalid_command_name(
    invalid_name: str,
) -> None:
    """The registry should reject malformed command names."""

    registry = CommandRegistry()

    with pytest.raises(ValueError):
        registry.register(
            ExampleCommand(name=invalid_name)
        )


def test_registry_reports_unknown_command() -> None:
    """The registry should report an unregistered command."""

    registry = CommandRegistry()

    with pytest.raises(
        CommandNotFoundError,
        match="not registered",
    ):
        registry.get("missing")


def test_registry_returns_deterministic_command_order() -> None:
    """Registry enumeration should be alphabetically deterministic."""

    registry = CommandRegistry()

    registry.register(ExampleCommand(name="status"))
    registry.register(ExampleCommand(name="compile"))
    registry.register(ExampleCommand(name="audit"))

    assert registry.names() == (
        "audit",
        "compile",
        "status",
    )

    assert tuple(
        command.name
        for command in registry
    ) == registry.names()


def test_registry_does_not_expose_mutable_storage() -> None:
    """Registry results should not expose its internal dictionary."""

    registry = CommandRegistry()
    registry.register(ExampleCommand())

    commands = registry.commands()

    assert isinstance(commands, tuple)
    assert commands == (registry.get("example"),)
