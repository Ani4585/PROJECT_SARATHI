"""Reusable repository audit engine for PROJECT SARATHI."""

from __future__ import annotations

import ast
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from scripts.tooling.git_tools import git_available


@dataclass(frozen=True, slots=True)
class AuditResult:
    """Represent the outcome of one repository audit check."""

    name: str
    passed: bool
    summary: str
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        name = self.name.strip()
        summary = self.summary.strip()
        details = tuple(detail.strip() for detail in self.details if detail.strip())
        if not name:
            raise ValueError("Audit result name must not be blank.")
        if not summary:
            raise ValueError("Audit result summary must not be blank.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "details", details)

    def to_dict(self) -> dict[str, object]:
        """Return a machine-readable result."""

        return {
            "name": self.name,
            "passed": self.passed,
            "summary": self.summary,
            "details": list(self.details),
        }


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Contain the deterministic results of a repository audit."""

    title: str
    results: tuple[AuditResult, ...]

    @property
    def passed_checks(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def failed_checks(self) -> int:
        return sum(not result.passed for result in self.results)

    @property
    def total_checks(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> bool:
        return self.failed_checks == 0

    def to_dict(self) -> dict[str, object]:
        """Return a machine-readable report."""

        return {
            "title": self.title,
            "summary": {
                "passed": self.passed_checks,
                "failed": self.failed_checks,
                "total": self.total_checks,
                "clean": self.passed,
            },
            "results": [result.to_dict() for result in self.results],
        }


AuditCheck = Callable[[Path], AuditResult]


class RepositoryAuditor:
    """Run an ordered collection of isolated repository checks."""

    def __init__(self, checks: Iterable[AuditCheck]) -> None:
        self._checks = tuple(checks)
        if not self._checks:
            raise ValueError("At least one repository audit check is required.")

    def run(self, project_root: Path) -> AuditReport:
        root = project_root.expanduser().resolve()
        results: list[AuditResult] = []
        for index, check in enumerate(self._checks, start=1):
            try:
                result = check(root)
            except Exception as error:  # A broken check must not abort the audit.
                result = AuditResult(
                    name=f"audit-check-{index}",
                    passed=False,
                    summary="The audit check raised an exception.",
                    details=(f"{type(error).__name__}: {error}",),
                )
            results.append(result)
        return AuditReport(
            title="PROJECT SARATHI Repository Audit",
            results=tuple(results),
        )


REQUIRED_DIRECTORIES = ("src", "scripts", "tests", "docs", "config")
REQUIRED_FILES = ("README.md", "sarathi.py", "pytest.ini", "src/core/version.py")


def check_repository_root(root: Path) -> AuditResult:
    passed = root.exists() and root.is_dir()
    return AuditResult(
        name="repository-root",
        passed=passed,
        summary="The repository root is valid." if passed else "The repository root is invalid.",
        details=(f"Root: {root}",),
    )


def check_required_directories(root: Path) -> AuditResult:
    missing = tuple(name for name in REQUIRED_DIRECTORIES if not (root / name).is_dir())
    return AuditResult(
        name="required-directories",
        passed=not missing,
        summary="All required directories exist." if not missing else "Required directories are missing.",
        details=("Missing: " + ", ".join(missing),) if missing else (f"Directories checked: {len(REQUIRED_DIRECTORIES)}",),
    )


def check_required_files(root: Path) -> AuditResult:
    missing = tuple(name for name in REQUIRED_FILES if not (root / name).is_file())
    return AuditResult(
        name="required-files",
        passed=not missing,
        summary="All required files exist." if not missing else "Required files are missing.",
        details=("Missing: " + ", ".join(missing),) if missing else (f"Files checked: {len(REQUIRED_FILES)}",),
    )


def check_python_sources(root: Path) -> AuditResult:
    source_files = tuple((root / "src").rglob("*.py")) if (root / "src").is_dir() else ()
    passed = bool(source_files)
    return AuditResult(
        name="python-sources",
        passed=passed,
        summary="Python source files were discovered." if passed else "No Python source files were discovered.",
        details=(f"Source files: {len(source_files)}",),
    )


def check_git_repository(root: Path) -> AuditResult:
    # git_available uses the active repository process context; the CLI executes at root.
    available = git_available()
    return AuditResult(
        name="git-repository",
        passed=available,
        summary="Git repository metadata is available." if available else "Git repository metadata is unavailable.",
        details=(f"Root: {root}",),
    )


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted((root / "src").rglob("*.py"))) if (root / "src").is_dir() else ()


def check_python_syntax(root: Path) -> AuditResult:
    """Parse every maintained source file and report syntax failures."""

    failures: list[str] = []
    files = _python_files(root)
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as error:
            failures.append(f"{path.relative_to(root)}: {type(error).__name__}: {error}")
    return AuditResult(
        name="python-syntax",
        passed=not failures and bool(files),
        summary="All Python sources parsed successfully." if not failures and files else "Python source parsing failed.",
        details=tuple(failures) if failures else (f"Files parsed: {len(files)}",),
    )


FORBIDDEN_DOMAIN_IMPORTS = (
    "config",
    "scripts",
    "src.application",
    "src.container",
    "src.infrastructure",
    "src.kernel",
)


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return tuple(modules)


def check_domain_boundaries(root: Path) -> AuditResult:
    """Enforce the inward-only dependency rule for domain code."""

    domain = root / "src" / "domain"
    files = tuple(sorted(domain.rglob("*.py"))) if domain.is_dir() else ()
    violations: list[str] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for module in _imported_modules(tree):
            if any(module == forbidden or module.startswith(forbidden + ".") for forbidden in FORBIDDEN_DOMAIN_IMPORTS):
                violations.append(f"{path.relative_to(root)} imports {module}")
    return AuditResult(
        name="domain-boundaries",
        passed=not violations,
        summary="Domain dependency boundaries are clean." if not violations else "Domain dependency violations were found.",
        details=tuple(violations) if violations else (f"Files checked: {len(files)}",),
    )


def check_composition_roots(root: Path) -> AuditResult:
    """Ensure executable composition roots remain small and declarative."""

    violations: list[str] = []
    checked = 0
    for relative in ("main.py", "sarathi.py"):
        path = root / relative
        if not path.is_file():
            violations.append(f"Missing: {relative}")
            continue
        checked += 1
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        main_functions = [
            node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main"
        ]
        if len(main_functions) != 1:
            violations.append(f"{relative}: expected exactly one main function")
            continue
        operational_statements = sum(
            isinstance(node, ast.stmt)
            for statement in main_functions[0].body
            for node in ast.walk(statement)
        )
        if operational_statements > 8:
            violations.append(f"{relative}: main contains {operational_statements} statements (maximum 8)")
    return AuditResult(
        name="composition-roots",
        passed=not violations and checked == 2,
        summary="Composition roots are thin." if not violations and checked == 2 else "Composition roots require attention.",
        details=tuple(violations) if violations else (f"Entry points checked: {checked}",),
    )


def check_official_roadmap(root: Path) -> AuditResult:
    """Ensure the authoritative programme source is repository-managed."""

    path = root / "docs" / "project_sarathi_master_roadmap.html"
    passed = path.is_file() and path.stat().st_size > 0
    return AuditResult(
        name="official-roadmap",
        passed=passed,
        summary="The official master roadmap is available." if passed else "The official master roadmap is missing or empty.",
        details=(f"Path: {path.relative_to(root)}",),
    )


def create_repository_auditor() -> RepositoryAuditor:
    """Create the standard deterministic repository and architecture auditor."""

    return RepositoryAuditor(
        (
            check_repository_root,
            check_required_directories,
            check_required_files,
            check_python_sources,
            check_git_repository,
            check_python_syntax,
            check_domain_boundaries,
            check_composition_roots,
            check_official_roadmap,
        )
    )


class AuditReportRenderer:
    """Render a repository audit as stable plain text."""

    def render(self, report: AuditReport) -> str:
        lines = [report.title, "=" * len(report.title), ""]
        for result in report.results:
            status = "PASS" if result.passed else "FAIL"
            lines.extend((f"[{status}] {result.name}", f"  {result.summary}"))
            lines.extend(f"  - {detail}" for detail in result.details)
            lines.append("")
        lines.extend(
            (
                f"Summary: {report.passed_checks} passed | {report.failed_checks} failed | {report.total_checks} total",
                "Overall: CLEAN" if report.passed else "Overall: ISSUES FOUND",
            )
        )
        return "\n".join(lines)


class AuditJsonRenderer:
    """Render a repository audit as stable JSON."""

    def render(self, report: AuditReport) -> str:
        return json.dumps(report.to_dict(), indent=2)
