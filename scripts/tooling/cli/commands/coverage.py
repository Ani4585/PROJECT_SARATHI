"""Source coverage CLI command."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections.abc import Callable

from scripts.tooling.console import print_header
from scripts.tooling.coverage import DEFAULT_COVERAGE_THRESHOLD
from scripts.tooling.verification import CommandResult, run_command

from ..command import Command
from ..context import CommandContext


CoverageExecutor = Callable[..., CommandResult]


class CoverageCommand(Command):
    """Run tests with source coverage collection and threshold enforcement."""

    def __init__(self, executor: CoverageExecutor = run_command) -> None:
        self._executor = executor

    @property
    def name(self) -> str:
        return "coverage"

    @property
    def description(self) -> str:
        return "Collect source coverage and enforce its threshold."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--threshold",
            type=float,
            default=DEFAULT_COVERAGE_THRESHOLD,
            help="Minimum source coverage percentage.",
        )

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        print_header("CLI - COVERAGE")
        result = self._executor(
            (
                context.python_executable,
                "scripts/coverage_report.py",
                "--threshold",
                str(arguments.threshold),
            ),
            cwd=context.project_root,
        )
        return result.return_code
