"""
Tests for the PROJECT SARATHI developer CLI entry point.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

import sarathi as sarathi_module
from scripts.tooling.version import get_version_information


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PROJECT_ROOT / "sarathi.py"


class RecordingApplication:
    """Record entry-point delegation for tests."""

    def __init__(
        self,
        exit_code: int,
    ) -> None:
        """Initialize the recording application.

        Args:
            exit_code: Exit code returned by the simulated application.
        """

        self._exit_code = exit_code
        self.arguments: Sequence[str] | None = None

    def run(
        self,
        arguments: Sequence[str] | None = None,
    ) -> int:
        """Record arguments and return the configured exit code."""

        self.arguments = arguments

        return self._exit_code


def run_entrypoint(
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    """Execute the real repository CLI entry point.

    Args:
        arguments: Command-line arguments passed to the CLI.

    Returns:
        The completed subprocess result.
    """

    return subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT),
            *arguments,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


@pytest.mark.parametrize(
    (
        "arguments",
        "expected_exit_code",
    ),
    (
        (
            None,
            0,
        ),
        (
            (
                "version",
            ),
            7,
        ),
    ),
)
def test_main_delegates_to_cli_application(
    monkeypatch: pytest.MonkeyPatch,
    arguments: Sequence[str] | None,
    expected_exit_code: int,
) -> None:
    """The entry point should delegate arguments and exit codes."""

    application = RecordingApplication(
        expected_exit_code
    )

    monkeypatch.setattr(
        sarathi_module,
        "create_cli_application",
        lambda: application,
    )

    exit_code = sarathi_module.main(
        arguments
    )

    assert exit_code == expected_exit_code
    assert application.arguments is arguments


def test_entrypoint_help_exposes_all_commands() -> None:
    """The executable help should expose every built-in command."""

    result = run_entrypoint(
        "--help"
    )

    assert result.returncode == 0

    for command_name in (
        "adr",
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
        assert command_name in result.stdout


def test_entrypoint_executes_version_command() -> None:
    """The executable should dispatch a real built-in command."""

    information = get_version_information()

    result = run_entrypoint(
        "version"
    )

    assert result.returncode == 0
    assert "CLI - VERSION" in result.stdout
    assert information.framework_name in result.stdout
    assert information.version in result.stdout
    assert information.milestone in result.stdout
    assert information.build_date in result.stdout


def test_entrypoint_rejects_unknown_command() -> None:
    """The executable should reject unknown command names."""

    result = run_entrypoint(
        "missing"
    )

    assert result.returncode == 2
    assert "invalid choice" in result.stderr
    assert "missing" in result.stderr

def test_entrypoint_executes_doctor_command() -> None:
    """The executable should run the real Framework Doctor."""

    result = run_entrypoint(
        "doctor"
    )

    assert result.returncode == 0
    assert "CLI - DOCTOR" in result.stdout
    assert (
        "Summary: 3 passed | 0 warnings | "
        "0 failed | 3 total"
    ) in result.stdout
    assert "Overall: HEALTHY" in result.stdout
