"""Unified developer dashboard aggregation, history, and report generation."""

from __future__ import annotations

import html
import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from src.health import HealthRunner, create_default_health_registry

from .audit import create_repository_auditor
from .benchmark import BenchmarkBaselineStore, BenchmarkRunner, create_default_benchmark_cases
from .version import get_version_information


class DashboardStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class DashboardSection:
    name: str
    status: DashboardStatus
    summary: str
    data: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status.value, "summary": self.summary, "data": dict(self.data)}


@dataclass(frozen=True, slots=True)
class DashboardReport:
    generated_at: str
    sections: tuple[DashboardSection, ...]
    changes: tuple[str, ...] = ()

    @property
    def status(self) -> DashboardStatus:
        if any(section.status is DashboardStatus.FAIL for section in self.sections):
            return DashboardStatus.FAIL
        if any(section.status is DashboardStatus.WARNING for section in self.sections):
            return DashboardStatus.WARNING
        return DashboardStatus.PASS

    @property
    def passed(self) -> bool:
        return self.status is not DashboardStatus.FAIL

    def to_dict(self) -> dict[str, object]:
        return {
            "title": "PROJECT SARATHI Developer Dashboard",
            "generated_at": self.generated_at,
            "summary": {"status": self.status.value, "passed": self.passed, "sections": len(self.sections)},
            "changes": list(self.changes),
            "sections": [section.to_dict() for section in self.sections],
        }


DashboardProvider = Callable[[], DashboardSection]


class DashboardCollector:
    def __init__(self, providers: Mapping[str, DashboardProvider], clock=lambda: datetime.now(timezone.utc)) -> None:
        self._providers = dict(providers)
        self._clock = clock

    def collect(self, selected: Iterable[str] | None = None) -> DashboardReport:
        names = tuple(sorted(selected or self._providers))
        sections: list[DashboardSection] = []
        for name in names:
            if name not in self._providers:
                sections.append(DashboardSection(name, DashboardStatus.FAIL, "Dashboard provider is not registered.", {}))
                continue
            try:
                section = self._providers[name]()
                if section.name != name:
                    raise ValueError("Dashboard provider returned a mismatched section name.")
                sections.append(section)
            except Exception as error:
                sections.append(
                    DashboardSection(name, DashboardStatus.FAIL, "Dashboard provider failed.", {"error": f"{type(error).__name__}: {error}"})
                )
        return DashboardReport(self._clock().isoformat(), tuple(sections))


def create_default_dashboard_collector(project_root: Path) -> DashboardCollector:
    root = project_root.resolve()

    def status() -> DashboardSection:
        version = get_version_information()
        return DashboardSection(
            "status", DashboardStatus.PASS, f"{version.version} / {version.milestone}", version.as_dict()
        )

    def health() -> DashboardSection:
        report = HealthRunner(create_default_health_registry(root)).run()
        state = DashboardStatus.PASS if report.passed else DashboardStatus.FAIL
        return DashboardSection("health", state, report.status.value, report.to_dict()["summary"])

    def coverage() -> DashboardSection:
        path = root / "reports" / "coverage" / "coverage.json"
        if not path.is_file():
            return DashboardSection("coverage", DashboardStatus.WARNING, "Coverage artifact is not available.", {})
        document = json.loads(path.read_text(encoding="utf-8"))
        summary = document["summary"]
        state = DashboardStatus.PASS if summary["passed"] else DashboardStatus.FAIL
        return DashboardSection("coverage", state, f"{summary['percentage']:.2f}%", summary)

    def audit() -> DashboardSection:
        report = create_repository_auditor().run(root)
        state = DashboardStatus.PASS if report.passed else DashboardStatus.FAIL
        return DashboardSection("audit", state, "clean" if report.passed else "issues found", report.to_dict()["summary"])

    def benchmarks() -> DashboardSection:
        baselines = BenchmarkBaselineStore(root / "config" / "benchmark_baselines.json").load()
        report = BenchmarkRunner().run(create_default_benchmark_cases(root), baselines)
        state = DashboardStatus.PASS if report.passed else DashboardStatus.FAIL
        return DashboardSection("benchmarks", state, f"{report.regressions} regressions", report.to_dict()["summary"])

    return DashboardCollector(
        {"audit": audit, "benchmarks": benchmarks, "coverage": coverage, "health": health, "status": status}
    )


class DashboardHistory:
    def __init__(self, path: Path) -> None:
        self.path = path

    def latest(self) -> dict[str, object] | None:
        if not self.path.is_file():
            return None
        lines = tuple(line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())
        return json.loads(lines[-1]) if lines else None

    def compare(self, report: DashboardReport) -> DashboardReport:
        previous = self.latest()
        if previous is None:
            return report
        old = {section["name"]: section["status"] for section in previous["sections"]}
        changes = tuple(
            f"{section.name}: {old.get(section.name, 'new')} -> {section.status.value}"
            for section in report.sections
            if old.get(section.name) != section.status.value
        )
        return DashboardReport(report.generated_at, report.sections, changes)

    def append(self, report: DashboardReport) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(report.to_dict(), sort_keys=True) + "\n")


class DashboardWriter:
    def write(self, report: DashboardReport, output: Path) -> tuple[Path, Path, Path]:
        output.mkdir(parents=True, exist_ok=True)
        json_path = output / "dashboard.json"
        html_path = output / "dashboard.html"
        summary_path = output / "dashboard-summary.json"
        json_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
        summary_path.write_text(json.dumps(report.to_dict()["summary"], indent=2) + "\n", encoding="utf-8")
        cards = "".join(
            f"<section><h2>{html.escape(section.name)}</h2><strong>{section.status.value.upper()}</strong>"
            f"<p>{html.escape(section.summary)}</p></section>" for section in report.sections
        )
        html_path.write_text(
            "<!doctype html><html><head><meta charset=\"utf-8\"><title>PROJECT SARATHI Dashboard</title>"
            "<style>body{font-family:system-ui;margin:2rem}section{border:1px solid #ccc;padding:1rem;margin:.5rem}</style>"
            f"</head><body><h1>PROJECT SARATHI Developer Dashboard</h1>{cards}</body></html>", encoding="utf-8"
        )
        return json_path, html_path, summary_path


class DashboardTextRenderer:
    def render(self, report: DashboardReport) -> str:
        lines = ["PROJECT SARATHI Developer Dashboard", "=" * 35]
        lines.extend(f"[{section.status.value.upper()}] {section.name}: {section.summary}" for section in report.sections)
        if report.changes:
            lines.extend(("", "Changes", *[f"- {change}" for change in report.changes]))
        lines.extend(("", f"Overall: {report.status.value.upper()}"))
        return "\n".join(lines)
