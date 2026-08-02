"""Deterministic benchmark execution, baselines, and regression reporting."""

from __future__ import annotations

import json
import platform
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from time import perf_counter


class BenchmarkStatus(StrEnum):
    """Describe one benchmark comparison outcome."""

    PASS = "pass"
    NEW = "new"
    REGRESSION = "regression"
    ERROR = "error"


class BenchmarkBaselineError(ValueError):
    """Raised when a stored benchmark baseline is invalid."""


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """Define one repeatable operation to measure."""

    name: str
    operation: Callable[[], object]
    iterations: int = 100
    warmups: int = 5

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Benchmark name must not be blank.")
        if self.iterations < 1:
            raise ValueError("Benchmark iterations must be positive.")
        if self.warmups < 0:
            raise ValueError("Benchmark warmups must not be negative.")
        object.__setattr__(self, "name", name)


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Contain the measurement and baseline comparison for one case."""

    name: str
    iterations: int
    mean_seconds: float
    baseline_seconds: float | None
    tolerance: float
    status: BenchmarkStatus
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.status in (BenchmarkStatus.PASS, BenchmarkStatus.NEW)

    @property
    def operations_per_second(self) -> float:
        return 0.0 if self.mean_seconds <= 0 else 1.0 / self.mean_seconds

    @property
    def change_percent(self) -> float | None:
        if self.baseline_seconds is None:
            return None
        return ((self.mean_seconds / self.baseline_seconds) - 1.0) * 100.0

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status.value,
            "iterations": self.iterations,
            "mean_seconds": self.mean_seconds,
            "operations_per_second": self.operations_per_second,
            "baseline_seconds": self.baseline_seconds,
            "tolerance": self.tolerance,
            "change_percent": self.change_percent,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Aggregate an ordered benchmark suite."""

    results: tuple[BenchmarkResult, ...]

    @property
    def passed(self) -> bool:
        return bool(self.results) and all(result.passed for result in self.results)

    @property
    def regressions(self) -> int:
        return sum(result.status is BenchmarkStatus.REGRESSION for result in self.results)

    @property
    def errors(self) -> int:
        return sum(result.status is BenchmarkStatus.ERROR for result in self.results)

    def to_dict(self) -> dict[str, object]:
        return {
            "title": "PROJECT SARATHI Benchmark Report",
            "environment": {
                "python": platform.python_version(),
                "implementation": platform.python_implementation(),
                "platform": platform.system(),
            },
            "summary": {
                "passed": self.passed,
                "benchmarks": len(self.results),
                "regressions": self.regressions,
                "errors": self.errors,
            },
            "results": [result.to_dict() for result in self.results],
        }


class BenchmarkRunner:
    """Measure benchmark cases and compare them with stored baselines."""

    def __init__(self, clock: Callable[[], float] = perf_counter) -> None:
        self._clock = clock

    def run(
        self,
        cases: Iterable[BenchmarkCase],
        baselines: Mapping[str, float] | None = None,
        *,
        tolerance: float = 0.25,
    ) -> BenchmarkReport:
        if tolerance < 0:
            raise ValueError("Benchmark tolerance must not be negative.")
        baseline_values = baselines or {}
        results: list[BenchmarkResult] = []
        for case in cases:
            baseline = baseline_values.get(case.name)
            try:
                for _ in range(case.warmups):
                    case.operation()
                started = self._clock()
                for _ in range(case.iterations):
                    case.operation()
                elapsed = max(0.0, self._clock() - started)
                mean = elapsed / case.iterations
                status = BenchmarkStatus.NEW
                if baseline is not None:
                    status = (
                        BenchmarkStatus.REGRESSION
                        if mean > baseline * (1.0 + tolerance)
                        else BenchmarkStatus.PASS
                    )
                results.append(
                    BenchmarkResult(case.name, case.iterations, mean, baseline, tolerance, status)
                )
            except Exception as error:
                results.append(
                    BenchmarkResult(
                        case.name,
                        case.iterations,
                        0.0,
                        baseline,
                        tolerance,
                        BenchmarkStatus.ERROR,
                        f"{type(error).__name__}: {error}",
                    )
                )
        return BenchmarkReport(tuple(results))


class BenchmarkBaselineStore:
    """Load and save versioned JSON benchmark baselines."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def load(self) -> dict[str, float]:
        if not self.path.is_file():
            return {}
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
            values = document["benchmarks"]
            if document.get("schema_version") != 1 or not isinstance(values, dict):
                raise BenchmarkBaselineError("Unsupported benchmark baseline schema.")
            baselines = {str(name): float(value) for name, value in values.items()}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            if isinstance(error, BenchmarkBaselineError):
                raise
            raise BenchmarkBaselineError(f"Invalid benchmark baseline: {error}") from error
        if any(not name.strip() or value <= 0 for name, value in baselines.items()):
            raise BenchmarkBaselineError("Benchmark baselines require names and positive durations.")
        return dict(sorted(baselines.items()))

    def save(self, report: BenchmarkReport) -> None:
        if not report.passed or any(result.mean_seconds <= 0 for result in report.results):
            raise BenchmarkBaselineError("Only successful positive benchmark results can become a baseline.")
        document = {
            "schema_version": 1,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "benchmarks": {
                result.name: result.mean_seconds for result in sorted(report.results, key=lambda item: item.name)
            },
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)


class BenchmarkTextRenderer:
    """Render benchmark results for people."""

    def render(self, report: BenchmarkReport) -> str:
        lines = ["PROJECT SARATHI Benchmark Report", "=" * 32]
        for result in report.results:
            lines.append(f"[{result.status.value.upper()}] {result.name}")
            if result.error:
                lines.append(f"  {result.error}")
                continue
            lines.append(f"  Mean: {result.mean_seconds * 1_000_000:.2f} us")
            lines.append(f"  Operations/second: {result.operations_per_second:,.2f}")
            if result.baseline_seconds is None:
                lines.append("  Baseline: not established")
            else:
                lines.append(f"  Baseline: {result.baseline_seconds * 1_000_000:.2f} us")
                lines.append(f"  Change: {result.change_percent:+.2f}%")
        lines.extend(
            [
                "",
                f"Summary: {len(report.results)} benchmarks | {report.regressions} regressions | {report.errors} errors",
                "Overall: PASS" if report.passed else "Overall: FAIL",
            ]
        )
        return "\n".join(lines)


class BenchmarkJsonRenderer:
    """Render benchmark results for automation."""

    def render(self, report: BenchmarkReport) -> str:
        return json.dumps(report.to_dict(), indent=2)


def create_default_benchmark_cases(project_root: Path) -> tuple[BenchmarkCase, ...]:
    """Create stable, dependency-free framework benchmarks."""

    from src.graph import DependencyGraph
    from src.reflection import ConstructorInspector

    class ExampleDependency:
        pass

    class ExampleService:
        def __init__(self, dependency: ExampleDependency) -> None:
            self.dependency = dependency

    def discover_sources() -> tuple[Path, ...]:
        return tuple((project_root / "src").rglob("*.py"))

    def inspect_constructor() -> list[type]:
        return ConstructorInspector.get_dependency_types(ExampleService)

    def build_graph() -> DependencyGraph:
        graph = DependencyGraph()
        graph.add_node(ExampleService)
        graph.add_node(ExampleDependency)
        graph.connect(ExampleService, ExampleDependency)
        return graph

    return (
        BenchmarkCase("repository-source-discovery", discover_sources, iterations=25, warmups=2),
        BenchmarkCase("constructor-inspection", inspect_constructor, iterations=500, warmups=20),
        BenchmarkCase("dependency-graph-build", build_graph, iterations=500, warmups=20),
    )
