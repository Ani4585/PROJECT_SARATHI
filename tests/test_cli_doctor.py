"""Tests for the PROJECT SARATHI Framework Doctor CLI command."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.tooling.cli.commands import DoctorCommand
from scripts.tooling.cli.context import CommandContext
from src.observability import (
    DiagnosticReport,
    DiagnosticResult,
    DiagnosticStatus,
)


class RecordingDoctor:
    """Return a configured report and record diagnostic execution."""

    def __init__(
        self,
        report: DiagnosticReport,
    ) -> None:
        """Initialize the recording doctor."""

        self._report = report
        self.run_count = 0

    def run(self) -> DiagnosticReport:
        """Record execution and return the configured report."""

        self.run_count += 1

        return self._report


class RecordingRenderer:
    """Render configured text and record received reports."""

    def __init__(
        self,
        rendered_text: str,
    ) -> None:
        """Initialize the recording renderer."""

        self._rendered_text = rendered_text
        self.reports: list[DiagnosticReport] = []

    def render(
        self,
        report: DiagnosticReport,
    ) -> str:
        """Record and render the supplied report."""

        self.reports.append(
            report
        )

        return self._rendered_text


def create_context(
    tmp_path: Path,
) -> CommandContext:
    """Create a temporary CLI execution context."""

    return CommandContext(
        project_root=tmp_path,
        python_executable=sys.executable,
    )


def create_report(
    status: DiagnosticStatus,
) -> DiagnosticReport:
    """Create a single-check diagnostic report."""

    return DiagnosticReport(
        title="Framework Doctor",
        results=(
            DiagnosticResult(
                name="test-check",
                status=status,
                summary="The test check completed.",
            ),
        ),
        duration_seconds=0.0,
    )


def test_doctor_command_exposes_metadata() -> None:
    """The Doctor command should expose stable CLI metadata."""

    command = DoctorCommand()

    assert command.name == "doctor"
    assert command.description == (
        "Run framework diagnostics."
    )


def test_doctor_command_executes_and_renders_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The command should run and render its injected diagnostics."""

    report = create_report(
        DiagnosticStatus.PASS
    )
    doctor = RecordingDoctor(
        report
    )
    renderer = RecordingRenderer(
        "rendered diagnostic report"
    )
    command = DoctorCommand(
        doctor=doctor,
        renderer=renderer,
    )

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="doctor"),
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert doctor.run_count == 1
    assert renderer.reports == [
        report,
    ]
    assert "CLI - DOCTOR" in output
    assert "rendered diagnostic report" in output


@pytest.mark.parametrize(
    (
        "status",
        "expected_exit_code",
    ),
    (
        (
            DiagnosticStatus.PASS,
            0,
        ),
        (
            DiagnosticStatus.WARNING,
            0,
        ),
        (
            DiagnosticStatus.FAIL,
            1,
        ),
    ),
)
def test_doctor_command_exit_code_matches_report_health(
    tmp_path: Path,
    status: DiagnosticStatus,
    expected_exit_code: int,
) -> None:
    """Only failed diagnostic checks should produce a failing exit."""

    report = create_report(
        status
    )
    command = DoctorCommand(
        doctor=RecordingDoctor(
            report
        ),
        renderer=RecordingRenderer(
            "diagnostic report"
        ),
    )

    exit_code = command.execute(
        create_context(tmp_path),
        Namespace(command="doctor"),
    )

    assert exit_code == expected_exit_code
