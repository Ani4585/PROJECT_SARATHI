"""
PROJECT SARATHI

Repository Verification Utilities

Provides reusable command execution, automated test,
compilation, and required-file verification.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence

from .coverage import DEFAULT_COVERAGE_THRESHOLD
from .filesystem import (
    PROJECT_ROOT,
    required_file_status,
)


@dataclass(frozen=True, slots=True)
class CommandResult:
    """
    Represents the result of an external command.
    """

    command: tuple[str, ...]
    return_code: int
    standard_output: str
    standard_error: str

    @property
    def passed(
        self,
    ) -> bool:
        """
        Return whether the command completed successfully.
        """

        return self.return_code == 0


def run_command(
    command: Sequence[str],
    *,
    cwd: Path = PROJECT_ROOT,
    capture_output: bool = False,
) -> CommandResult:
    """
    Execute a command and return a structured result.

    Operating-system execution errors are converted into
    failed command results instead of crashing the tooling.
    """

    normalized_command = tuple(
        str(part)
        for part in command
    )

    try:
        completed = subprocess.run(
            list(normalized_command),
            cwd=cwd,
            check=False,
            text=True,
            capture_output=capture_output,
        )

    except OSError as error:
        return CommandResult(
            command=normalized_command,
            return_code=1,
            standard_output="",
            standard_error=str(error),
        )

    return CommandResult(
        command=normalized_command,
        return_code=completed.returncode,
        standard_output=(
            completed.stdout
            if capture_output
            else ""
        ),
        standard_error=(
            completed.stderr
            if capture_output
            else ""
        ),
    )

def run_tests(
    *,
    verbose: bool = True,
) -> CommandResult:
    """
    Run the automated pytest suite.
    """

    command = [
        sys.executable,
        "-m",
        "pytest",
    ]

    if verbose:
        command.append(
            "-v"
        )

    return run_command(
        command
    )


def run_coverage(
    *,
    threshold: float = DEFAULT_COVERAGE_THRESHOLD,
) -> CommandResult:
    """Run tests with source coverage collection and threshold enforcement."""

    return run_command(
        [
            sys.executable,
            "scripts/coverage_report.py",
            "--threshold",
            str(threshold),
        ]
    )


def run_benchmarks() -> CommandResult:
    """Run the standard performance regression suite."""

    return run_command(
        [
            sys.executable,
            "sarathi.py",
            "benchmark",
        ]
    )


def run_developer_report() -> CommandResult:
    """Generate and validate dependency, environment, and tooling reports."""

    return run_command(
        [
            sys.executable,
            "sarathi.py",
            "report",
            "--format",
            "json",
        ]
    )


def run_cli_plugin_audit() -> CommandResult:
    """Verify installed CLI command extensions load cleanly."""

    return run_command(
        [
            sys.executable,
            "sarathi.py",
            "plugins",
            "--format",
            "json",
        ]
    )


def run_health_monitoring() -> CommandResult:
    """Run all operational health groups with machine-readable output."""

    return run_command(
        [
            sys.executable,
            "sarathi.py",
            "monitor",
            "--format",
            "json",
        ]
    )


def run_runtime_diagnostics() -> CommandResult:
    """Generate a redacted, safe-share runtime diagnostic bundle."""

    return run_command(
        [
            sys.executable,
            "sarathi.py",
            "diagnostics",
            "--format",
            "json",
        ]
    )


def run_adr_validation() -> CommandResult:
    """Validate managed Architecture Decision Records and their links."""

    return run_command([sys.executable, "sarathi.py", "adr", "validate"])


def run_dashboard() -> CommandResult:
    """Generate the unified dashboard and CI summary artifacts."""

    return run_command([sys.executable, "sarathi.py", "dashboard", "--format", "json"])


def run_compilation() -> CommandResult:
    """
    Compile the source and tooling packages.
    """

    return run_command(
        [
            sys.executable,
            "-m",
            "compileall",
            "src",
            "config",
            "scripts",
        ]
    )


def verify_required_files(
    required_files: tuple[str, ...],
) -> dict[str, bool]:
    """
    Check mandatory repository files.
    """

    return required_file_status(
        required_files
    )


def all_required_files_exist(
    required_files: tuple[str, ...],
) -> bool:
    """
    Return whether every required file exists.
    """

    statuses = verify_required_files(
        required_files
    )

    return all(
        statuses.values()
    )
