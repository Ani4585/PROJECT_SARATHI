"""
PROJECT SARATHI

Framework Doctor CLI Command

Provides the thin command-line adapter between the reusable
framework observability engine and the developer CLI.
"""

from __future__ import annotations

from argparse import Namespace
from typing import Protocol

from src.observability import (
    DiagnosticReport,
    DiagnosticReportRenderer,
    create_framework_doctor,
)

from ...console import print_header
from ..command import Command
from ..context import CommandContext


class _DiagnosticRunner(Protocol):
    """Describe an object capable of running diagnostics."""

    def run(self) -> DiagnosticReport:
        """Run diagnostics and return a typed report."""


class _DiagnosticRenderer(Protocol):
    """Describe an object capable of rendering diagnostics."""

    def render(
        self,
        report: DiagnosticReport,
    ) -> str:
        """Render a typed diagnostic report."""


class DoctorCommand(Command):
    """Execute and display framework diagnostics."""

    def __init__(
        self,
        doctor: _DiagnosticRunner | None = None,
        renderer: _DiagnosticRenderer | None = None,
    ) -> None:
        """Initialize the Doctor command.

        Args:
            doctor: Diagnostic runner used by the command.
            renderer: Report renderer used by the command.
        """

        self._doctor = (
            doctor
            if doctor is not None
            else create_framework_doctor()
        )
        self._renderer = (
            renderer
            if renderer is not None
            else DiagnosticReportRenderer()
        )

    @property
    def name(self) -> str:
        """Return the command name."""

        return "doctor"

    @property
    def description(self) -> str:
        """Return the command help description."""

        return "Run framework diagnostics."

    def execute(
        self,
        context: CommandContext,
        arguments: Namespace,
    ) -> int:
        """Run diagnostics and translate health into an exit code.

        Args:
            context: Shared CLI execution context.
            arguments: Parsed command-line arguments.

        Returns:
            Zero when no diagnostic check failed; otherwise one.
        """

        del context
        del arguments

        print_header(
            "CLI - DOCTOR"
        )

        report = self._doctor.run()

        print(
            self._renderer.render(
                report
            )
        )

        return (
            1
            if report.failed_checks
            else 0
        )
