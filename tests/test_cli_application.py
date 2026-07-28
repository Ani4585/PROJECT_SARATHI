"""
Tests for the PROJECT SARATHI developer CLI application.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import pytest

from scripts.tooling.cli.application import CliApplication
from scripts.tooling.cli.command import Command
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.cli.registry import CommandRegistry


class RecordingCommand(Command):
    """Record command configuration and execution for tests."""

    def __init__(
        self,
        name: str = "example",
        description: str = "Execute an example command.",
        exit_code: int = 0,
    ) -> None:
        """Initialize the recording command.

        Args:
            name: Command name exposed by the parser.
            description: Command help description.
            exit_code: Exit code returned during execution.
        """

        self._name = name
        self._description = description
        self._exit_code = exit_code
        self.parser_configured = False
        self.execution_context: CommandContext | None = None
        self.execution_arguments: Namespace | None = None

    @property
    def name(self) -> str:
        """Return the command name."""

        return self._name

    @property
    def description(self) -> str:
        """Return the command description."""

        return self._description

    def configure_parser(
        self,
        parser: ArgumentParser,
    ) -> None:
        """Add a controllable command option."""

        self.parser_configured = True

        parser.add_argument(
            "--value",
            default="default",
        )

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Record execution inputs and return the configured exit code."""

        self.execution_context = context
        self.execution_arguments = arguments

        return self._exit_code


def create_application(
    tmp_path: Path,
    *commands: RecordingCommand,
) -> tuple[CliApplication, CommandContext]:
    """Create a CLI application for testing.

    Args:
        tmp_path: Temporary repository path.
        commands: Commands to register.

    Returns:
        The application and its shared execution context.
    """

    registry = CommandRegistry()

    for command in commands:
        registry.register(command)

    context = CommandContext(
        project_root=tmp_path,
        python_executable=sys.executable,
    )

    application = CliApplication(
        registry,
        context,
    )

    return application, context


def test_application_builds_parser_from_registry(
    tmp_path: Path,
) -> None:
    """The parser should include registered command configuration."""

    command = RecordingCommand()
    application, _ = create_application(
        tmp_path,
        command,
    )

    parser = application.build_parser()
    arguments = parser.parse_args(
        [
            "example",
            "--value",
            "configured",
        ]
    )

    assert command.parser_configured is True
    assert arguments.command == "example"
    assert arguments.value == "configured"


def test_application_help_lists_registered_commands(
    tmp_path: Path,
) -> None:
    """Root help should describe every registered command."""

    application, _ = create_application(
        tmp_path,
        RecordingCommand(
            name="status",
            description="Display project status.",
        ),
        RecordingCommand(
            name="audit",
            description="Run project auditing.",
        ),
    )

    help_text = application.build_parser().format_help()

    assert "status" in help_text
    assert "Display project status." in help_text
    assert "audit" in help_text
    assert "Run project auditing." in help_text


def test_application_dispatches_selected_command(
    tmp_path: Path,
) -> None:
    """The selected command should receive context and arguments."""

    command = RecordingCommand()
    application, context = create_application(
        tmp_path,
        command,
    )

    exit_code = application.run(
        [
            "example",
            "--value",
            "selected",
        ]
    )

    assert exit_code == 0
    assert command.execution_context is context
    assert command.execution_arguments is not None
    assert command.execution_arguments.value == "selected"


def test_application_propagates_command_exit_code(
    tmp_path: Path,
) -> None:
    """The application should return the command exit code unchanged."""

    command = RecordingCommand(
        exit_code=7
    )
    application, _ = create_application(
        tmp_path,
        command,
    )

    assert application.run(["example"]) == 7


def test_application_executes_only_selected_command(
    tmp_path: Path,
) -> None:
    """Dispatch should not execute commands that were not selected."""

    first = RecordingCommand(
        name="first"
    )
    second = RecordingCommand(
        name="second"
    )

    application, _ = create_application(
        tmp_path,
        first,
        second,
    )

    exit_code = application.run(
        ["second"]
    )

    assert exit_code == 0
    assert first.execution_context is None
    assert second.execution_context is not None


def test_application_requires_command(
    tmp_path: Path,
) -> None:
    """The parser should reject an invocation without a command."""

    application, _ = create_application(
        tmp_path,
        RecordingCommand(),
    )

    with pytest.raises(SystemExit) as error:
        application.run([])

    assert error.value.code == 2


def test_application_rejects_unknown_command(
    tmp_path: Path,
) -> None:
    """The parser should reject an unregistered command name."""

    application, _ = create_application(
        tmp_path,
        RecordingCommand(),
    )

    with pytest.raises(SystemExit) as error:
        application.run(["missing"])

    assert error.value.code == 2
