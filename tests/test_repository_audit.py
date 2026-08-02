"""Tests for the reusable PROJECT SARATHI repository audit engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.tooling.audit import (
    AuditJsonRenderer,
    AuditReportRenderer,
    AuditResult,
    RepositoryAuditor,
    check_python_sources,
    check_repository_root,
    check_composition_roots,
    check_domain_boundaries,
    check_official_roadmap,
    check_python_syntax,
)


def test_audit_result_normalizes_text() -> None:
    result = AuditResult(" check ", True, " complete ", (" detail ", " "))
    assert result.name == "check"
    assert result.summary == "complete"
    assert result.details == ("detail",)


@pytest.mark.parametrize("field", ("name", "summary"))
def test_audit_result_rejects_blank_required_text(field: str) -> None:
    values = {"name": "check", "summary": "complete"}
    values[field] = " "
    with pytest.raises(ValueError):
        AuditResult(passed=True, **values)


def test_repository_auditor_runs_checks_in_order(tmp_path: Path) -> None:
    calls: list[str] = []

    def first(root: Path) -> AuditResult:
        calls.append(f"first:{root.name}")
        return AuditResult("first", True, "First passed.")

    def second(root: Path) -> AuditResult:
        calls.append(f"second:{root.name}")
        return AuditResult("second", False, "Second failed.")

    report = RepositoryAuditor((first, second)).run(tmp_path)
    assert calls == [f"first:{tmp_path.name}", f"second:{tmp_path.name}"]
    assert report.passed_checks == 1
    assert report.failed_checks == 1
    assert report.passed is False


def test_repository_auditor_isolates_check_exceptions(tmp_path: Path) -> None:
    def broken(root: Path) -> AuditResult:
        del root
        raise RuntimeError("boom")

    report = RepositoryAuditor((broken,)).run(tmp_path)
    assert report.failed_checks == 1
    assert "RuntimeError: boom" in report.results[0].details


def test_repository_auditor_rejects_empty_checks() -> None:
    with pytest.raises(ValueError):
        RepositoryAuditor(())


def test_standard_checks_detect_root_and_python_sources(tmp_path: Path) -> None:
    source = tmp_path / "src" / "example"
    source.mkdir(parents=True)
    (source / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    assert check_repository_root(tmp_path).passed is True
    assert check_python_sources(tmp_path).passed is True


def test_audit_renderer_reports_failure() -> None:
    report = RepositoryAuditor((lambda root: AuditResult("check", False, "Failed."),)).run(Path.cwd())
    rendered = AuditReportRenderer().render(report)
    assert "[FAIL] check" in rendered
    assert "Overall: ISSUES FOUND" in rendered


def test_audit_report_supports_machine_readable_output() -> None:
    report = RepositoryAuditor((lambda root: AuditResult("check", True, "Passed."),)).run(Path.cwd())
    rendered = AuditJsonRenderer().render(report)
    assert '"clean": true' in rendered
    assert '"name": "check"' in rendered


def test_python_syntax_check_reports_parse_failures(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "broken.py").write_text("if:\n", encoding="utf-8")
    result = check_python_syntax(tmp_path)
    assert result.passed is False
    assert "SyntaxError" in result.details[0]


def test_domain_boundary_check_rejects_outward_import(tmp_path: Path) -> None:
    domain = tmp_path / "src" / "domain"
    domain.mkdir(parents=True)
    (domain / "model.py").write_text("from src.infrastructure import database\n", encoding="utf-8")
    result = check_domain_boundaries(tmp_path)
    assert result.passed is False
    assert "src.infrastructure" in result.details[0]


def test_composition_root_check_accepts_thin_entry_points(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (tmp_path / "sarathi.py").write_text("def main():\n    return 0\n", encoding="utf-8-sig")
    assert check_composition_roots(tmp_path).passed is True


def test_official_roadmap_check_requires_nonempty_file(tmp_path: Path) -> None:
    roadmap = tmp_path / "docs" / "project_sarathi_master_roadmap.html"
    roadmap.parent.mkdir()
    roadmap.write_text("roadmap", encoding="utf-8")
    assert check_official_roadmap(tmp_path).passed is True
