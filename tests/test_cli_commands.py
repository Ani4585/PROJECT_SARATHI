"""
Tests for the PROJECT SARATHI developer CLI built-in commands.
"""

from __future__ import annotations

import sys
from argparse import Namespace
from collections.abc import Sequence
from pathlib import Path

import pytest

from scripts.tooling.cli.commands import (
    CompilationCommand,
    ScriptCommand,
    TestCommand as CliTestCommand,
    VersionCommand,
)
from scripts.tooling.cli.commands import compilation as compilation_module
from scripts.tooling.cli.commands import script as script_module
from scripts.tooling.cli.commands import testing as testing_module
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.verification import CommandResult
from scripts.tooling.version import get_version_information


def create_context(
    tmp_path: Path,
) -> CommandContext:
    """Create a command context for a temporary repository.

    Args:
        tmp_path: Temporary repository root.

    Returns:
        A CLI context using the active Python interpreter.
    """

    return CommandContext(
        project_root=tmp_path,
        python_executable=sys.executable,
    )


def create_result(
    command: Sequence[str],
    return_code: int,
) -> CommandResult:
    """Create a structured command result for testing.

    Args:
        command: Executed command components.
        return_code: Simulated process exit code.

    Returns:
        A command result containing the supplied values.
    """

    return CommandResult(
        command=tuple(command),
        return_code=return_code,
        standard_output="",
        standard_error="",
    )


def test_script_command_exposes_configuration() -> None:
    """A script command should expose its configured metadata."""

    command = ScriptCommand(
        name="status",
        description="Display project status.",
        script_path="scripts/project_status.py",
    )

    assert command.name == "status"
    assert command.description == "Display project status."
    assert command.script_path == Path(
        "scripts/project_status.py"
    )


def test_script_command_executes_repository_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A script command should use the context interpreter and root."""

    script_file = (
        tmp_path
        / "scripts"
        / "example.py"
    )

    script_file.parent.mkdir()
    script_file.write_text(
        "print('example')\n",
        encoding="utf-8",
    )

    recorded_calls: list[
        tuple[tuple[str, ...], Path]
    ] = []

    def fake_run_command(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> CommandResult:
        """Record a simulated subprocess call."""

        normalized_command = tuple(command)

        recorded_calls.append(
            (
                normalized_command,
                cwd,
            )
        )

        return create_result(
            normalized_command,
            0,
        )

    monkeypatch.setattr(
        script_module,
        "run_command",
        fake_run_command,
    )

    command = ScriptCommand(
        name="example",
        description="Execute an example script.",
        script_path="scripts/example.py",
    )

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="example"),
    )

    assert exit_code == 0
    assert recorded_calls == [
        (
            (
                sys.executable,
                str(script_file),
            ),
            tmp_path.resolve(),
        )
    ]

    assert "CLI - EXAMPLE" in (
        capsys.readouterr().out
    )


def test_script_command_propagates_failure_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A script command should return a failing script exit code."""

    script_file = (
        tmp_path
        / "scripts"
        / "failing.py"
    )

    script_file.parent.mkdir()
    script_file.write_text(
        "raise SystemExit(6)\n",
        encoding="utf-8",
    )

    def fake_run_command(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> CommandResult:
        """Return a simulated script failure."""

        del cwd

        return create_result(
            command,
            6,
        )

    monkeypatch.setattr(
        script_module,
        "run_command",
        fake_run_command,
    )

    command = ScriptCommand(
        name="failing",
        description="Execute a failing script.",
        script_path="scripts/failing.py",
    )

    assert command.execute(
        create_context(tmp_path),
        Namespace(command="failing"),
    ) == 6


def test_script_command_reports_missing_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing script should fail without starting a process."""

    def unexpected_run_command(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> CommandResult:
        """Reject unexpected process execution."""

        del command
        del cwd

        raise AssertionError(
            "A missing script must not be executed."
        )

    monkeypatch.setattr(
        script_module,
        "run_command",
        unexpected_run_command,
    )

    command = ScriptCommand(
        name="missing",
        description="Execute a missing script.",
        script_path="scripts/missing.py",
    )

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="missing"),
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "ERROR:" in output
    assert "scripts" in output
    assert "missing.py" in output


def test_test_command_exposes_metadata() -> None:
    """The native test command should expose stable metadata."""

    command = CliTestCommand()

    assert command.name == "test"
    assert command.description == (
        "Run the complete pytest suite."
    )


@pytest.mark.parametrize(
    "return_code",
    (
        0,
        5,
    ),
)
def test_test_command_constructs_and_propagates_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    return_code: int,
) -> None:
    """The test command should construct pytest and propagate its result."""

    recorded_calls: list[
        tuple[tuple[str, ...], Path]
    ] = []

    def fake_run_command(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> CommandResult:
        """Record the simulated pytest process."""

        normalized_command = tuple(command)

        recorded_calls.append(
            (
                normalized_command,
                cwd,
            )
        )

        return create_result(
            normalized_command,
            return_code,
        )

    monkeypatch.setattr(
        testing_module,
        "run_command",
        fake_run_command,
    )

    command = CliTestCommand()
    context = create_context(tmp_path)

    assert command.execute(
        context,
        Namespace(command="test"),
    ) == return_code

    assert recorded_calls == [
        (
            (
                sys.executable,
                "-m",
                "pytest",
                "-v",
            ),
            tmp_path.resolve(),
        )
    ]


def test_compilation_command_exposes_complete_targets() -> None:
    """Compilation should include every maintained Python location."""

    command = CompilationCommand()

    assert command.name == "compile"
    assert command.description == (
        "Compile source, configuration, scripts, and tests."
    )

    assert command.targets == (
        "src",
        "config",
        "scripts",
        "tests",
        "sarathi.py",
    )


@pytest.mark.parametrize(
    "return_code",
    (
        0,
        4,
    ),
)
def test_compilation_command_constructs_and_propagates_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    return_code: int,
) -> None:
    """Compilation should use compileall and propagate its result."""

    recorded_calls: list[
        tuple[tuple[str, ...], Path]
    ] = []

    def fake_run_command(
        command: Sequence[str],
        *,
        cwd: Path,
    ) -> CommandResult:
        """Record the simulated compilation process."""

        normalized_command = tuple(command)

        recorded_calls.append(
            (
                normalized_command,
                cwd,
            )
        )

        return create_result(
            normalized_command,
            return_code,
        )

    monkeypatch.setattr(
        compilation_module,
        "run_command",
        fake_run_command,
    )

    command = CompilationCommand()
    context = create_context(tmp_path)

    assert command.execute(
        context,
        Namespace(command="compile"),
    ) == return_code

    assert recorded_calls == [
        (
            (
                sys.executable,
                "-m",
                "compileall",
                "src",
                "config",
                "scripts",
                "tests",
                "sarathi.py",
            ),
            tmp_path.resolve(),
        )
    ]


def test_version_command_exposes_metadata() -> None:
    """The version command should expose stable command metadata."""

    command = VersionCommand()

    assert command.name == "version"
    assert command.description == (
        "Display PROJECT SARATHI version information."
    )


def test_version_command_displays_authoritative_information(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Version output should use the authoritative metadata source."""

    command = VersionCommand()
    information = get_version_information()

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="version"),
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "CLI - VERSION" in output
    assert information.framework_name in output
    assert information.version in output
    assert information.milestone in output
    assert information.build_date in output
