"""
PROJECT SARATHI

Developer Command-Line Interface

Provides one consistent entry point for repository
status, statistics, health checks, and release verification.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


COMMAND_SCRIPTS = {
    "stats": PROJECT_ROOT / "scripts" / "repository_stats.py",
    "status": PROJECT_ROOT / "scripts" / "project_status.py",
    "health": PROJECT_ROOT / "scripts" / "health_check.py",
    "release": PROJECT_ROOT / "scripts" / "release_gate.py",
}


def run_script(
    script: Path,
    extra_arguments: Sequence[str] = (),
) -> int:
    """
    Execute one PROJECT SARATHI developer script.
    """

    if not script.exists():
        print(f"ERROR: Developer script not found: {script}")
        return 1

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            *extra_arguments,
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    return completed.returncode


def run_verify() -> int:
    """
    Run complete repository verification.

    Repository statistics and project status are displayed
    before the release gate performs tests, compilation,
    metadata validation, required-file validation, and Git checks.
    """

    commands = (
        "stats",
        "status",
        "release",
    )

    for command in commands:
        print()
        print("=" * 60)
        print(f"PROJECT SARATHI CLI — {command.upper()}")
        print("=" * 60)

        return_code = run_script(
            COMMAND_SCRIPTS[command]
        )

        if return_code != 0:
            print()
            print("=" * 60)
            print(f"VERIFICATION STOPPED: {command.upper()} FAILED")
            print("=" * 60)
            return return_code

    print()
    print("=" * 60)
    print("PROJECT SARATHI")
    print("MILESTONE 11.5 VERIFICATION COMPLETE")
    print("READY FOR COMMIT")
    print("=" * 60)

    return 0


def build_parser() -> argparse.ArgumentParser:
    """
    Build the PROJECT SARATHI command parser.
    """

    parser = argparse.ArgumentParser(
        prog="sarathi",
        description=(
            "PROJECT SARATHI developer tooling command-line interface."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "stats",
        help="Display repository statistics.",
    )

    subparsers.add_parser(
        "status",
        help="Display framework, repository, and Git status.",
    )

    subparsers.add_parser(
        "health",
        help="Run automated tests and compilation checks.",
    )

    subparsers.add_parser(
        "release",
        help="Run the release gate.",
    )

    subparsers.add_parser(
        "verify",
        help="Run complete one-command repository verification.",
    )

    subparsers.add_parser(
        "test",
        help="Run the complete pytest suite.",
    )

    subparsers.add_parser(
        "compile",
        help="Compile source, configuration, scripts, and tests.",
    )

    subparsers.add_parser(
        "version",
        help="Display PROJECT SARATHI version information.",
    )

    return parser


def run_tests() -> int:
    """
    Run the complete automated test suite.
    """

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-v",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    return completed.returncode


def run_compilation() -> int:
    """
    Compile all maintained Python directories.
    """

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "src",
            "config",
            "scripts",
            "tests",
            "sarathi.py",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    return completed.returncode


def show_version() -> int:
    """
    Display framework version metadata.
    """

    from src.core.version import (
        BUILD_DATE,
        FRAMEWORK_NAME,
        MILESTONE,
        VERSION,
    )

    print("=" * 60)
    print(FRAMEWORK_NAME)
    print("Version Information")
    print("=" * 60)
    print(f"{'Version':<25}: {VERSION}")
    print(f"{'Milestone':<25}: {MILESTONE}")
    print(f"{'Build Date':<25}: {BUILD_DATE}")

    return 0


def main(
    arguments: Sequence[str] | None = None,
) -> int:
    """
    Execute the requested developer command.
    """

    parser = build_parser()
    parsed = parser.parse_args(arguments)

    if parsed.command == "verify":
        return run_verify()

    if parsed.command == "test":
        return run_tests()

    if parsed.command == "compile":
        return run_compilation()

    if parsed.command == "version":
        return show_version()

    script = COMMAND_SCRIPTS.get(
        parsed.command
    )

    if script is None:
        parser.error(
            f"Unknown command: {parsed.command}"
        )

    return run_script(script)


if __name__ == "__main__":
    raise SystemExit(main())