"""Dependency, environment, and tooling report generation."""

from __future__ import annotations

import html
import json
import platform
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from pathlib import Path


class ReportStatus(StrEnum):
    """Describe the health of one reported fact."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class ReportItem:
    """Represent one named developer-environment fact."""

    name: str
    value: str
    status: ReportStatus = ReportStatus.PASS

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "value": self.value, "status": self.status.value}


@dataclass(frozen=True, slots=True)
class ReportSection:
    """Group related report items."""

    name: str
    items: tuple[ReportItem, ...]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "items": [item.to_dict() for item in self.items]}


@dataclass(frozen=True, slots=True)
class DeveloperReport:
    """Contain the complete M12.6 developer report."""

    sections: tuple[ReportSection, ...]

    @property
    def failures(self) -> int:
        return sum(item.status is ReportStatus.FAIL for section in self.sections for item in section.items)

    @property
    def warnings(self) -> int:
        return sum(item.status is ReportStatus.WARNING for section in self.sections for item in section.items)

    @property
    def passed(self) -> bool:
        return bool(self.sections) and self.failures == 0

    def to_dict(self) -> dict[str, object]:
        return {
            "title": "PROJECT SARATHI Developer Report",
            "summary": {
                "passed": self.passed,
                "sections": len(self.sections),
                "warnings": self.warnings,
                "failures": self.failures,
            },
            "sections": [section.to_dict() for section in self.sections],
        }


class DeveloperReportCollector:
    """Collect dependency, runtime environment, and tooling facts."""

    def __init__(self, package_version: Callable[[str], str] = metadata.version) -> None:
        self._package_version = package_version

    def collect(self, project_root: Path) -> DeveloperReport:
        root = project_root.resolve()
        return DeveloperReport(
            (
                self._collect_dependencies(root),
                self._collect_environment(root),
                self._collect_tooling(root),
            )
        )

    def _collect_dependencies(self, root: Path) -> ReportSection:
        requirements = root / "requirements.txt"
        if not requirements.is_file():
            return ReportSection(
                "Dependencies",
                (ReportItem("requirements.txt", "missing", ReportStatus.FAIL),),
            )
        try:
            raw_requirements = requirements.read_bytes()
            encoding = (
                "utf-16"
                if raw_requirements.startswith((b"\xff\xfe", b"\xfe\xff"))
                else "utf-8-sig"
            )
            requirement_lines = raw_requirements.decode(encoding).splitlines()
        except (OSError, UnicodeError) as error:
            return ReportSection(
                "Dependencies",
                (
                    ReportItem(
                        "requirements.txt",
                        f"unreadable: {type(error).__name__}: {error}",
                        ReportStatus.FAIL,
                    ),
                ),
            )
        items: list[ReportItem] = []
        for line in requirement_lines:
            specification = line.strip()
            if not specification or specification.startswith("#"):
                continue
            name, separator, expected = specification.partition("==")
            if not separator or not name or not expected:
                items.append(ReportItem(specification, "not exactly pinned", ReportStatus.WARNING))
                continue
            try:
                installed = self._package_version(name)
            except metadata.PackageNotFoundError:
                items.append(ReportItem(name, f"missing; expected {expected}", ReportStatus.WARNING))
                continue
            status = ReportStatus.PASS if installed == expected else ReportStatus.WARNING
            items.append(ReportItem(name, f"installed {installed}; expected {expected}", status))
        return ReportSection("Dependencies", tuple(items))

    def _collect_environment(self, root: Path) -> ReportSection:
        supported = sys.version_info >= (3, 14)
        return ReportSection(
            "Environment",
            (
                ReportItem(
                    "Python",
                    platform.python_version(),
                    ReportStatus.PASS if supported else ReportStatus.WARNING,
                ),
                ReportItem("Implementation", platform.python_implementation()),
                ReportItem("Operating system", platform.platform()),
                ReportItem("Architecture", platform.machine() or "unknown"),
                ReportItem("Virtual environment", "active" if sys.prefix != sys.base_prefix else "inactive"),
                ReportItem("Project root", str(root)),
            ),
        )

    def _collect_tooling(self, root: Path) -> ReportSection:
        git = shutil.which("git")
        try:
            pytest_version = self._package_version("pytest")
        except metadata.PackageNotFoundError:
            pytest_version = "not installed"
        return ReportSection(
            "Tooling",
            (
                ReportItem("Python executable", sys.executable),
                ReportItem("Git executable", git or "not found", ReportStatus.PASS if git else ReportStatus.WARNING),
                ReportItem(
                    "pytest",
                    pytest_version,
                    ReportStatus.PASS if pytest_version != "not installed" else ReportStatus.WARNING,
                ),
                ReportItem(
                    "pytest.ini",
                    "present" if (root / "pytest.ini").is_file() else "missing",
                    ReportStatus.PASS if (root / "pytest.ini").is_file() else ReportStatus.FAIL,
                ),
                ReportItem("Python source files", str(len(tuple((root / "src").rglob("*.py"))))),
                ReportItem("Test files", str(len(tuple((root / "tests").glob("test_*.py"))))),
            ),
        )


class DeveloperReportTextRenderer:
    """Render a developer report for terminal use."""

    def render(self, report: DeveloperReport) -> str:
        lines = ["PROJECT SARATHI Developer Report", "=" * 32]
        for section in report.sections:
            lines.extend(("", section.name, "-" * len(section.name)))
            for item in section.items:
                lines.append(f"[{item.status.value.upper()}] {item.name}: {item.value}")
        lines.extend(
            (
                "",
                f"Summary: {len(report.sections)} sections | {report.warnings} warnings | {report.failures} failures",
                "Overall: PASS" if report.passed else "Overall: FAIL",
            )
        )
        return "\n".join(lines)


class DeveloperReportJsonRenderer:
    """Render a developer report for automation."""

    def render(self, report: DeveloperReport) -> str:
        return json.dumps(report.to_dict(), indent=2)


class DeveloperReportWriter:
    """Persist developer reports as JSON and standalone HTML."""

    def write(self, report: DeveloperReport, output: Path) -> tuple[Path, Path]:
        output.mkdir(parents=True, exist_ok=True)
        json_path = output / "developer-report.json"
        html_path = output / "developer-report.html"
        json_path.write_text(DeveloperReportJsonRenderer().render(report) + "\n", encoding="utf-8")
        rows = "".join(
            f"<tr><td>{html.escape(section.name)}</td><td>{html.escape(item.name)}</td>"
            f"<td>{html.escape(item.value)}</td><td>{item.status.value}</td></tr>"
            for section in report.sections
            for item in section.items
        )
        html_path.write_text(
            "<!doctype html><html><head><meta charset=\"utf-8\"><title>PROJECT SARATHI Developer Report</title>"
            "<style>body{font-family:system-ui;margin:2rem}table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #ccc;padding:.4rem;text-align:left}</style></head><body>"
            f"<h1>PROJECT SARATHI Developer Report</h1><p>Overall: {'PASS' if report.passed else 'FAIL'}</p>"
            f"<table><thead><tr><th>Section</th><th>Name</th><th>Value</th><th>Status</th></tr></thead><tbody>{rows}"
            "</tbody></table></body></html>",
            encoding="utf-8",
        )
        return json_path, html_path
