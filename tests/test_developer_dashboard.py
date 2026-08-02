"""Tests for official M18 developer dashboard."""

from __future__ import annotations

import json
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path

from scripts.tooling.cli.commands.dashboard import DashboardCommand
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.dashboard import (
    DashboardCollector,
    DashboardHistory,
    DashboardReport,
    DashboardSection,
    DashboardStatus,
    DashboardTextRenderer,
    DashboardWriter,
    create_default_dashboard_collector,
)


NOW = datetime(2026, 8, 2, tzinfo=timezone.utc)


def section(name: str, status: DashboardStatus = DashboardStatus.PASS) -> DashboardSection:
    return DashboardSection(name, status, f"{name} summary", {"value": name})


def test_report_aggregates_failures_and_warnings() -> None:
    passing = DashboardReport(NOW.isoformat(), (section("status"),))
    warning = DashboardReport(NOW.isoformat(), (section("coverage", DashboardStatus.WARNING),))
    failing = DashboardReport(NOW.isoformat(), (section("audit", DashboardStatus.FAIL),))
    assert passing.status is DashboardStatus.PASS
    assert warning.status is DashboardStatus.WARNING and warning.passed is True
    assert failing.status is DashboardStatus.FAIL and failing.passed is False


def test_collector_filters_and_sorts_sections() -> None:
    collector = DashboardCollector(
        {"zeta": lambda: section("zeta"), "alpha": lambda: section("alpha")},
        clock=lambda: NOW,
    )
    report = collector.collect(("zeta", "alpha"))
    assert tuple(item.name for item in report.sections) == ("alpha", "zeta")
    assert report.generated_at == NOW.isoformat()


def test_collector_isolates_provider_failure_and_unknown_section() -> None:
    def broken():
        raise RuntimeError("boom")

    report = DashboardCollector({"broken": broken}, clock=lambda: NOW).collect(("broken", "missing"))
    assert tuple(item.status for item in report.sections) == (DashboardStatus.FAIL, DashboardStatus.FAIL)
    assert report.sections[0].data["error"] == "RuntimeError: boom"


def test_history_appends_and_reports_status_changes(tmp_path: Path) -> None:
    history = DashboardHistory(tmp_path / "history.jsonl")
    first = DashboardReport(NOW.isoformat(), (section("health"),))
    history.append(first)
    current = DashboardReport(NOW.isoformat(), (section("health", DashboardStatus.WARNING), section("audit")))
    compared = history.compare(current)
    assert compared.changes == ("health: pass -> warning", "audit: new -> pass")
    history.append(compared)
    assert history.latest()["summary"]["sections"] == 2


def test_writer_generates_json_html_and_ci_summary(tmp_path: Path) -> None:
    report = DashboardReport(NOW.isoformat(), (DashboardSection("status", DashboardStatus.PASS, "<safe>", {}),))
    json_path, html_path, summary_path = DashboardWriter().write(report, tmp_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["passed"] is True
    assert json.loads(summary_path.read_text(encoding="utf-8"))["status"] == "pass"
    html = html_path.read_text(encoding="utf-8")
    assert "&lt;safe&gt;" in html and "<safe>" not in html


def test_text_renderer_includes_changes() -> None:
    report = DashboardReport(NOW.isoformat(), (section("health"),), ("health: warning -> pass",))
    rendered = DashboardTextRenderer().render(report)
    assert "[PASS] health" in rendered
    assert "health: warning -> pass" in rendered


def test_default_collector_treats_missing_coverage_as_warning(tmp_path: Path) -> None:
    report = create_default_dashboard_collector(tmp_path).collect(("coverage", "status"))
    assert tuple(item.name for item in report.sections) == ("coverage", "status")
    assert report.sections[0].status is DashboardStatus.WARNING
    assert report.passed is True


def test_dashboard_command_generates_filtered_artifacts(tmp_path: Path, capsys) -> None:
    output = tmp_path / "dashboard"
    exit_code = DashboardCommand().execute(
        CommandContext(tmp_path, "python"),
        Namespace(section=["coverage", "status"], format="json", output=output),
    )
    rendered = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert rendered["summary"]["sections"] == 2
    assert (output / "dashboard.html").is_file()
    assert (output / "dashboard-summary.json").is_file()
    assert (output / "history.jsonl").is_file()
