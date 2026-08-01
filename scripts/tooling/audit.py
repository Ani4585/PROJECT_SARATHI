"""Reusable repository audit engine for PROJECT SARATHI."""

from __future__ import annotations

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


def create_repository_auditor() -> RepositoryAuditor:
    """Create the standard deterministic five-check repository auditor."""

    return RepositoryAuditor(
        (
            check_repository_root,
            check_required_directories,
            check_required_files,
            check_python_sources,
            check_git_repository,
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
