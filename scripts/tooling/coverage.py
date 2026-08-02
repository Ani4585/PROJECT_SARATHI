"""Dependency-free source coverage collection and reporting."""

from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from trace import Trace


DEFAULT_COVERAGE_THRESHOLD = 85.0


@dataclass(frozen=True, slots=True)
class FileCoverage:
    """Coverage result for one Python source file."""

    path: str
    statements: int
    covered: int
    missing: tuple[int, ...]

    @property
    def percentage(self) -> float:
        return 100.0 if self.statements == 0 else self.covered / self.statements * 100.0


@dataclass(frozen=True, slots=True)
class CoverageReport:
    """Aggregate source coverage and test-process status."""

    files: tuple[FileCoverage, ...]
    threshold: float
    test_exit_code: int

    @property
    def statements(self) -> int:
        return sum(file.statements for file in self.files)

    @property
    def covered(self) -> int:
        return sum(file.covered for file in self.files)

    @property
    def percentage(self) -> float:
        return 100.0 if self.statements == 0 else self.covered / self.statements * 100.0

    @property
    def passed(self) -> bool:
        return self.test_exit_code == 0 and self.percentage >= self.threshold


def discover_source_files(source_root: Path) -> tuple[Path, ...]:
    """Discover maintained Python files in deterministic order."""

    return tuple(sorted(path.resolve() for path in source_root.rglob("*.py") if "__pycache__" not in path.parts))


def executable_lines(path: Path) -> frozenset[int]:
    """Return AST statement lines, excluding documentation-only expressions."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    documentation_lines: set[int] = set()
    for parent in ast.walk(tree):
        body = getattr(parent, "body", None)
        if body and isinstance(body, list):
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                documentation_lines.add(first.lineno)
    return frozenset(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt) and node.lineno not in documentation_lines
    )


def build_coverage_report(
    source_root: Path,
    counts: dict[tuple[str, int], int],
    *,
    threshold: float = DEFAULT_COVERAGE_THRESHOLD,
    test_exit_code: int = 0,
) -> CoverageReport:
    """Build a report from trace.py execution counts."""

    if not 0.0 <= threshold <= 100.0:
        raise ValueError("Coverage threshold must be between 0 and 100.")
    normalized_counts = {
        (str(Path(filename).resolve()).casefold(), line): count
        for (filename, line), count in counts.items()
    }
    files: list[FileCoverage] = []
    root = source_root.resolve()
    for path in discover_source_files(root):
        statements = executable_lines(path)
        covered_lines = {
            line
            for line in statements
            if normalized_counts.get((str(path).casefold(), line), 0) > 0
        }
        missing = tuple(sorted(statements - covered_lines))
        files.append(
            FileCoverage(
                path=path.relative_to(root.parent).as_posix(),
                statements=len(statements),
                covered=len(covered_lines),
                missing=missing,
            )
        )
    return CoverageReport(tuple(files), float(threshold), int(test_exit_code))


class CoverageReportWriter:
    """Render coverage results for consoles, automation, and browsers."""

    def render_text(self, report: CoverageReport) -> str:
        status = "PASS" if report.passed else "FAIL"
        lines = [
            "PROJECT SARATHI Source Coverage",
            "================================",
            f"Files: {len(report.files)}",
            f"Statements: {report.statements}",
            f"Covered: {report.covered}",
            f"Coverage: {report.percentage:.2f}%",
            f"Threshold: {report.threshold:.2f}%",
            f"Tests: {'PASS' if report.test_exit_code == 0 else f'FAIL ({report.test_exit_code})'}",
            f"Overall: {status}",
        ]
        return "\n".join(lines)

    def write_json(self, report: CoverageReport, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": {
                "files": len(report.files),
                "statements": report.statements,
                "covered": report.covered,
                "percentage": round(report.percentage, 4),
                "threshold": report.threshold,
                "test_exit_code": report.test_exit_code,
                "passed": report.passed,
            },
            "files": [
                {**asdict(file), "percentage": round(file.percentage, 4)}
                for file in report.files
            ],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def write_html(self, report: CoverageReport, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = "".join(
            "<tr>"
            f"<td>{escape(file.path)}</td>"
            f"<td>{file.statements}</td>"
            f"<td>{file.covered}</td>"
            f"<td>{file.percentage:.2f}%</td>"
            f"<td>{escape(', '.join(map(str, file.missing)))}</td>"
            "</tr>"
            for file in report.files
        )
        status = "PASS" if report.passed else "FAIL"
        document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>PROJECT SARATHI Coverage</title>
<style>body{{font-family:system-ui;margin:2rem}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:.4rem;text-align:left}}th{{background:#eee}}</style></head>
<body><h1>PROJECT SARATHI Source Coverage</h1>
<p><strong>{report.percentage:.2f}%</strong> coverage; threshold {report.threshold:.2f}%; overall {status}.</p>
<table><thead><tr><th>File</th><th>Statements</th><th>Covered</th><th>Coverage</th><th>Missing lines</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
        path.write_text(document, encoding="utf-8")


def collect_pytest_coverage(
    project_root: Path,
    *,
    threshold: float = DEFAULT_COVERAGE_THRESHOLD,
    pytest_arguments: tuple[str, ...] = ("-q", "-p", "no:cacheprovider"),
) -> CoverageReport:
    """Run pytest under the standard-library tracer and build a source report."""

    tracer = Trace(count=True, trace=False)

    def run_tests() -> int:
        import pytest

        return int(pytest.main(list(pytest_arguments)))

    original_directory = Path.cwd()
    try:
        import os

        os.chdir(project_root)
        test_exit_code = int(tracer.runfunc(run_tests))
    finally:
        os.chdir(original_directory)
    return build_coverage_report(
        project_root / "src",
        tracer.results().counts,
        threshold=threshold,
        test_exit_code=test_exit_code,
    )
