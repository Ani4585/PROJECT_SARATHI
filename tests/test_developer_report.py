"""Tests for official M12.6 developer reports."""

from __future__ import annotations

import json
from argparse import Namespace
from importlib import metadata
from pathlib import Path

import pytest

from scripts.tooling.cli.commands.report import ReportCommand
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.developer_report import (
    DeveloperReport,
    DeveloperReportCollector,
    DeveloperReportJsonRenderer,
    DeveloperReportTextRenderer,
    DeveloperReportWriter,
    ReportItem,
    ReportSection,
    ReportStatus,
)


def prepare_project(root: Path, requirements: str = "") -> None:
    (root / "requirements.txt").write_text(requirements, encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")


def test_collector_creates_three_ordered_sections(tmp_path: Path) -> None:
    prepare_project(tmp_path, "example==1.0\n")
    report = DeveloperReportCollector(lambda name: "1.0").collect(tmp_path)
    assert tuple(section.name for section in report.sections) == (
        "Dependencies",
        "Environment",
        "Tooling",
    )
    assert report.sections[0].items[0].status is ReportStatus.PASS
    assert report.passed is True


def test_dependency_report_warns_for_mismatch_missing_and_unpinned(tmp_path: Path) -> None:
    prepare_project(tmp_path, "different==2.0\nmissing==1.0\nunpinned>=1\n")

    def version(name: str) -> str:
        if name == "missing":
            raise metadata.PackageNotFoundError(name)
        if name == "pytest":
            return "9.0"
        return "1.0"

    report = DeveloperReportCollector(version).collect(tmp_path)
    dependencies = report.sections[0]
    assert tuple(item.status for item in dependencies.items) == (
        ReportStatus.WARNING,
        ReportStatus.WARNING,
        ReportStatus.WARNING,
    )
    assert report.warnings >= 3
    assert report.passed is True


def test_dependency_report_reads_utf16_windows_requirements(tmp_path: Path) -> None:
    prepare_project(tmp_path)
    (tmp_path / "requirements.txt").write_text("example==1.0\n", encoding="utf-16")
    report = DeveloperReportCollector(lambda name: "1.0").collect(tmp_path)
    assert report.sections[0].items[0].name == "example"
    assert report.sections[0].items[0].status is ReportStatus.PASS


def test_missing_requirements_is_a_failure(tmp_path: Path) -> None:
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    report = DeveloperReportCollector(lambda name: "1.0").collect(tmp_path)
    assert report.sections[0].items[0].status is ReportStatus.FAIL
    assert report.passed is False


def test_report_renderers_expose_status() -> None:
    report = DeveloperReport(
        (ReportSection("Environment", (ReportItem("Python", "3.14"),)),)
    )
    assert "[PASS] Python: 3.14" in DeveloperReportTextRenderer().render(report)
    document = json.loads(DeveloperReportJsonRenderer().render(report))
    assert document["summary"]["passed"] is True


def test_writer_generates_json_and_escaped_html(tmp_path: Path) -> None:
    report = DeveloperReport(
        (ReportSection("Tools", (ReportItem("Name", "<safe>"),)),)
    )
    json_path, html_path = DeveloperReportWriter().write(report, tmp_path / "reports")
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["passed"] is True
    html = html_path.read_text(encoding="utf-8")
    assert "&lt;safe&gt;" in html
    assert "<safe>" not in html


def test_report_command_writes_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    prepare_project(tmp_path)
    exit_code = ReportCommand().execute(
        CommandContext(tmp_path, "python"),
        Namespace(format="text", output=Path("reports/developer")),
    )
    assert exit_code == 0
    assert (tmp_path / "reports" / "developer" / "developer-report.json").is_file()
    assert (tmp_path / "reports" / "developer" / "developer-report.html").is_file()
    assert "PROJECT SARATHI Developer Report" in capsys.readouterr().out


def test_report_command_json_has_no_cli_banner(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    prepare_project(tmp_path)
    exit_code = ReportCommand().execute(
        CommandContext(tmp_path, "python"),
        Namespace(format="json", output=Path("reports/developer")),
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CLI - REPORT" not in output
    assert json.loads(output)["summary"]["passed"] is True
