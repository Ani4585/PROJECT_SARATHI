"""Tests for official M12.3 source coverage collection."""

from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.tooling.cli.commands.coverage import CoverageCommand
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.coverage import (
    CoverageReportWriter,
    build_coverage_report,
    discover_source_files,
    executable_lines,
)
from scripts.tooling.verification import CommandResult


def write_source(root: Path, name: str, content: str) -> Path:
    path = root / "src" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_source_discovery_is_recursive_and_deterministic(tmp_path: Path) -> None:
    second = write_source(tmp_path, "zeta.py", "VALUE = 1\n")
    first = write_source(tmp_path, "alpha/module.py", "VALUE = 1\n")
    assert discover_source_files(tmp_path / "src") == (
        first.resolve(),
        second.resolve(),
    )


def test_executable_lines_exclude_module_and_function_docstrings(tmp_path: Path) -> None:
    path = write_source(
        tmp_path,
        "sample.py",
        '\"\"\"module docs\"\"\"\nVALUE = 1\n\ndef work():\n    \"\"\"function docs\"\"\"\n    return VALUE\n',
    )
    assert executable_lines(path) == frozenset({2, 4, 6})


def test_report_calculates_aggregate_coverage(tmp_path: Path) -> None:
    path = write_source(tmp_path, "sample.py", "VALUE = 1\nOTHER = 2\n")
    report = build_coverage_report(
        tmp_path / "src",
        {(str(path.resolve()), 1): 1},
        threshold=50,
    )
    assert report.statements == 2
    assert report.covered == 1
    assert report.percentage == 50.0
    assert report.passed is True
    assert report.files[0].missing == (2,)


def test_report_fails_threshold_or_tests(tmp_path: Path) -> None:
    write_source(tmp_path, "sample.py", "VALUE = 1\n")
    below = build_coverage_report(tmp_path / "src", {}, threshold=1)
    failed_tests = build_coverage_report(
        tmp_path / "src", {}, threshold=0, test_exit_code=2
    )
    assert below.passed is False
    assert failed_tests.passed is False


@pytest.mark.parametrize("threshold", (-1, 101))
def test_report_rejects_invalid_threshold(tmp_path: Path, threshold: float) -> None:
    with pytest.raises(ValueError):
        build_coverage_report(tmp_path, {}, threshold=threshold)


def test_writer_creates_json_and_html_reports(tmp_path: Path) -> None:
    path = write_source(tmp_path, "sample.py", "VALUE = 1\n")
    report = build_coverage_report(
        tmp_path / "src", {(str(path.resolve()), 1): 1}, threshold=70
    )
    writer = CoverageReportWriter()
    json_path = tmp_path / "reports" / "coverage.json"
    html_path = tmp_path / "reports" / "coverage.html"
    writer.write_json(report, json_path)
    writer.write_html(report, html_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["passed"] is True
    assert "sample.py" in html_path.read_text(encoding="utf-8")
    assert "Overall: PASS" in writer.render_text(report)


def test_coverage_command_exposes_metadata_and_parser() -> None:
    command = CoverageCommand()
    assert command.name == "coverage"
    assert command.description == "Collect source coverage and enforce its threshold."


def test_coverage_command_executes_report_script(tmp_path: Path) -> None:
    calls: list[tuple[tuple[str, ...], Path]] = []

    def execute(command, *, cwd, **kwargs):
        del kwargs
        calls.append((tuple(command), cwd))
        return CommandResult(tuple(command), 0, "", "")

    command = CoverageCommand(execute)
    context = CommandContext(tmp_path, sys.executable)
    assert command.execute(context, Namespace(command="coverage", threshold=75.0)) == 0
    assert calls == [
        (
            (
                sys.executable,
                "scripts/coverage_report.py",
                "--threshold",
                "75.0",
            ),
            tmp_path.resolve(),
        )
    ]


def test_coverage_report_script_bootstraps_repository_imports() -> None:
    project_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "scripts/coverage_report.py", "--help"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Collect PROJECT SARATHI source coverage" in completed.stdout
