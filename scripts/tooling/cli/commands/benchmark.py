"""Benchmark runner CLI command."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections.abc import Callable
from pathlib import Path

from scripts.tooling.benchmark import (
    BenchmarkBaselineError,
    BenchmarkBaselineStore,
    BenchmarkCase,
    BenchmarkJsonRenderer,
    BenchmarkRunner,
    BenchmarkTextRenderer,
    create_default_benchmark_cases,
)

from ...console import print_error, print_header
from ..command import Command
from ..context import CommandContext


class BenchmarkCommand(Command):
    """Run the standard benchmark suite and detect regressions."""

    def __init__(
        self,
        runner: BenchmarkRunner | None = None,
        cases_factory: Callable[[Path], tuple[BenchmarkCase, ...]] = create_default_benchmark_cases,
    ) -> None:
        self._runner = runner or BenchmarkRunner()
        self._cases_factory = cases_factory

    @property
    def name(self) -> str:
        return "benchmark"

    @property
    def description(self) -> str:
        return "Run benchmarks and detect performance regressions."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--baseline",
            type=Path,
            default=Path("config/benchmark_baselines.json"),
            help="Versioned JSON baseline file.",
        )
        parser.add_argument(
            "--tolerance",
            type=float,
            default=0.25,
            help="Allowed fractional slowdown before a regression is reported.",
        )
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument(
            "--update-baseline",
            action="store_true",
            help="Replace the baseline with successful measurements.",
        )

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        output_format = getattr(arguments, "format", "text")
        if output_format == "text":
            print_header("CLI - BENCHMARK")
        baseline_argument = getattr(arguments, "baseline", Path("config/benchmark_baselines.json"))
        baseline_path = baseline_argument if baseline_argument.is_absolute() else context.project_root / baseline_argument
        store = BenchmarkBaselineStore(baseline_path)
        try:
            baselines = {} if getattr(arguments, "update_baseline", False) else store.load()
            report = self._runner.run(
                self._cases_factory(context.project_root),
                baselines,
                tolerance=getattr(arguments, "tolerance", 0.25),
            )
            if getattr(arguments, "update_baseline", False) and report.passed:
                store.save(report)
        except (BenchmarkBaselineError, ValueError) as error:
            print_error(str(error))
            return 2
        renderer = BenchmarkJsonRenderer() if output_format == "json" else BenchmarkTextRenderer()
        print(renderer.render(report))
        if getattr(arguments, "update_baseline", False) and report.passed and output_format == "text":
            print(f"Baseline updated: {store.path}")
        return 0 if report.passed else 1
