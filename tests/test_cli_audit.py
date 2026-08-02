"""Tests for the PROJECT SARATHI Repository Audit CLI command."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.tooling.audit import AuditReport, AuditResult
from scripts.tooling.cli.commands import AuditCommand
from scripts.tooling.cli.context import CommandContext


class RecordingAuditor:
    def __init__(self, report: AuditReport) -> None:
        self.report = report
        self.roots: list[Path] = []

    def run(self, project_root: Path) -> AuditReport:
        self.roots.append(project_root)
        return self.report


class RecordingRenderer:
    def __init__(self) -> None:
        self.reports: list[AuditReport] = []

    def render(self, report: AuditReport) -> str:
        self.reports.append(report)
        return "rendered audit"


def make_report(passed: bool) -> AuditReport:
    return AuditReport("Audit", (AuditResult("check", passed, "Complete."),))


def test_audit_command_exposes_metadata() -> None:
    command = AuditCommand()
    assert command.name == "audit"
    assert command.description == "Audit repository structure and integrity."


@pytest.mark.parametrize(("passed", "expected"), ((True, 0), (False, 1)))
def test_audit_command_renders_and_returns_health(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    passed: bool,
    expected: int,
) -> None:
    report = make_report(passed)
    auditor = RecordingAuditor(report)
    renderer = RecordingRenderer()
    command = AuditCommand(auditor=auditor, renderer=renderer)
    context = CommandContext(tmp_path, sys.executable)
    exit_code = command.execute(context, Namespace(command="audit"))
    output = capsys.readouterr().out
    assert exit_code == expected
    assert auditor.roots == [tmp_path.resolve()]
    assert renderer.reports == [report]
    assert "CLI - AUDIT" in output
    assert "rendered audit" in output


def test_audit_command_can_render_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    command = AuditCommand(auditor=RecordingAuditor(make_report(True)))
    context = CommandContext(tmp_path, sys.executable)
    assert command.execute(context, Namespace(command="audit", format="json")) == 0
    output = capsys.readouterr().out
    assert '"clean": true' in output
    assert "CLI - AUDIT" not in output
