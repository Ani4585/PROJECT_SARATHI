"""
Tests for built-in registration and composite CLI verification.
"""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.tooling.cli.application import create_cli_application
from scripts.tooling.cli.command import Command
from scripts.tooling.cli.commands import (
    ScriptCommand,
    VerificationCommand,
)
from scripts.tooling.cli.commands.builtins import (
    create_builtin_registry,
    register_builtin_commands,
)
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.cli.registry import (
    CommandAlreadyRegisteredError,
    CommandRegistry,
)
from scripts.tooling.version import get_version_information


class RecordingCommand(Command):
    """Record composite-command execution for verification tests."""

    def __init__(
        self,
        name: str,
        executions: list[str],
        exit_code: int = 0,
    ) -> None:
        """Initialize the recording command.

        Args:
            name: Command name exposed to the registry.
            executions: Mutable execution record used by the test.
            exit_code: Exit code returned during execution.
        """

        self._name = name
        self._executions = executions
        self._exit_code = exit_code

    @property
    def name(self) -> str:
        """Return the recording command name."""

        return self._name

    @property
    def description(self) -> str:
        """Return the recording command description."""

        return f"Execute {self.name}."

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Record execution and return the configured exit code."""

        del context

        assert arguments.command == self.name

        self._executions.append(
            self.name
        )

        return self._exit_code


def create_context(
    tmp_path: Path,
) -> CommandContext:
    """Create a temporary CLI execution context.

    Args:
        tmp_path: Temporary repository root.

    Returns:
        A CLI context using the active interpreter.
    """

    return CommandContext(
        project_root=tmp_path,
        python_executable=sys.executable,
    )


def create_verification_registry(
    executions: list[str],
    *,
    status_exit_code: int = 0,
) -> CommandRegistry:
    """Create a registry containing verification test commands.

    Args:
        executions: Mutable command execution record.
        status_exit_code: Exit code returned by the status command.

    Returns:
        A registry containing the three verification steps.
    """

    registry = CommandRegistry()

    registry.register(
        RecordingCommand(
            "stats",
            executions,
        )
    )
    registry.register(
        RecordingCommand(
            "status",
            executions,
            exit_code=status_exit_code,
        )
    )
    registry.register(
        RecordingCommand(
            "release",
            executions,
        )
    )

    return registry


def test_verification_command_exposes_metadata() -> None:
    """Verification should expose stable metadata and ordering."""

    registry = CommandRegistry()
    command = VerificationCommand(registry)

    assert command.name == "verify"
    assert command.description == (
        "Run complete one-command repository verification."
    )
    assert command.sequence == (
        "stats",
        "status",
        "release",
    )


def test_verification_executes_steps_in_order(
    tmp_path: Path,
) -> None:
    """Verification should execute every configured command in order."""

    executions: list[str] = []
    registry = create_verification_registry(
        executions
    )
    command = VerificationCommand(registry)

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="verify"),
    )

    assert exit_code == 0
    assert executions == [
        "stats",
        "status",
        "release",
    ]


def test_verification_stops_at_first_failure(
    tmp_path: Path,
) -> None:
    """Verification should stop immediately after a failed command."""

    executions: list[str] = []
    registry = create_verification_registry(
        executions,
        status_exit_code=7,
    )
    command = VerificationCommand(registry)

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="verify"),
    )

    assert exit_code == 7
    assert executions == [
        "stats",
        "status",
    ]


def test_verification_reports_success(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Successful verification should display completion information."""

    executions: list[str] = []
    registry = create_verification_registry(
        executions
    )
    command = VerificationCommand(registry)
    information = get_version_information()

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="verify"),
    )

    output = capsys.readouterr().out
    milestone_number = (
        information.milestone.removeprefix("M")
    )

    assert exit_code == 0
    assert information.framework_name in output
    assert (
        f"MILESTONE {milestone_number} "
        "VERIFICATION COMPLETE"
    ) in output
    assert "READY FOR COMMIT" in output


def test_builtin_registry_exposes_all_commands() -> None:
    """The built-in registry should expose every established command."""

    registry = create_builtin_registry()

    assert registry.names() == (
        "adr",
        "audit",
        "benchmark",
        "compile",
        "coverage",
        "dashboard",
        "diagnostics",
        "doctor",
        "health",
        "monitor",
        "plugins",
        "release",
        "report",
        "stats",
        "status",
        "test",
        "verify",
        "version",
    )


def test_builtin_registry_preserves_script_mappings() -> None:
    """Script-backed commands should preserve their established files."""

    registry = create_builtin_registry()

    mappings = {
        name: registry.get(name).script_path
        for name in (
            "stats",
            "status",
            "health",
            "release",
        )
    }

    assert mappings == {
        "stats": Path(
            "scripts/repository_stats.py"
        ),
        "status": Path(
            "scripts/project_status.py"
        ),
        "health": Path(
            "scripts/health_check.py"
        ),
        "release": Path(
            "scripts/release_gate.py"
        ),
    }


def test_builtin_registry_preserves_help_descriptions() -> None:
    """Built-in commands should preserve the M11.5 help contract."""

    registry = create_builtin_registry()

    descriptions = {
        command.name: command.description
        for command in registry
    }

    assert descriptions == {
        "adr": "Create and manage architecture decision records.",
        "audit": "Audit repository structure and integrity.",
        "benchmark": "Run benchmarks and detect performance regressions.",
        "compile": (
            "Compile source, configuration, scripts, and tests."
        ),
        "coverage": "Collect source coverage and enforce its threshold.",
        "dashboard": "Generate the unified developer dashboard.",
        "diagnostics": "Generate a redacted runtime diagnostic bundle.",
        "doctor": "Run framework diagnostics.",
        "health": (
            "Run automated tests and compilation checks."
        ),
        "monitor": "Run grouped operational health checks.",
        "plugins": "Inspect installed CLI command extensions.",
        "release": "Run the release gate.",
        "report": "Generate dependency, environment, and tooling reports.",
        "stats": "Display repository statistics.",
        "status": (
            "Display framework, repository, and Git status."
        ),
        "test": "Run the complete pytest suite.",
        "verify": (
            "Run complete one-command repository verification."
        ),
        "version": (
            "Display PROJECT SARATHI version information."
        ),
    }


def test_builtin_registration_rejects_duplicate_names() -> None:
    """Built-in registration should retain duplicate protection."""

    registry = CommandRegistry()

    registry.register(
        ScriptCommand(
            name="stats",
            description="Existing command.",
            script_path="scripts/existing.py",
        )
    )

    with pytest.raises(
        CommandAlreadyRegisteredError,
    ):
        register_builtin_commands(
            registry
        )


def test_cli_factory_builds_every_subparser(
    tmp_path: Path,
) -> None:
    """The standard factory should make every command parseable."""

    application = create_cli_application(
        create_context(tmp_path)
    )
    parser = application.build_parser()

    for command_name in (
        "compile",
        "benchmark",
        "coverage",
        "dashboard",
        "diagnostics",
        "doctor",
        "health",
        "monitor",
        "plugins",
        "release",
        "report",
        "stats",
        "status",
        "test",
        "verify",
        "version",
    ):
        arguments = parser.parse_args(
            [command_name]
        )

        assert arguments.command == command_name

    adr_arguments = parser.parse_args(["adr", "list"])
    assert adr_arguments.command == "adr"
    assert adr_arguments.adr_action == "list"


def test_cli_factory_dispatches_version_command(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The standard application should dispatch a real built-in command."""

    application = create_cli_application(
        create_context(tmp_path)
    )

    exit_code = application.run(
        ["version"]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "CLI - VERSION" in output
    assert get_version_information().version in output
