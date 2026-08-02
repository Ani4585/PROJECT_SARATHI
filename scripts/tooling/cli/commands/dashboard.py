"""Unified developer dashboard CLI command."""

from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path

from scripts.tooling.dashboard import (
    DashboardHistory,
    DashboardTextRenderer,
    DashboardWriter,
    create_default_dashboard_collector,
)

from ...console import print_header
from ..command import Command
from ..context import CommandContext


class DashboardCommand(Command):
    @property
    def name(self) -> str:
        return "dashboard"

    @property
    def description(self) -> str:
        return "Generate the unified developer dashboard."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--section",
            action="append",
            choices=("status", "health", "coverage", "audit", "benchmarks"),
        )
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument("--output", type=Path, default=Path("reports/dashboard"))

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        output_format = getattr(arguments, "format", "text")
        if output_format == "text":
            print_header("CLI - DASHBOARD")
        collector = create_default_dashboard_collector(context.project_root)
        report = collector.collect(getattr(arguments, "section", None))
        output_argument = getattr(arguments, "output", Path("reports/dashboard"))
        output = output_argument if output_argument.is_absolute() else context.project_root / output_argument
        history = DashboardHistory(output / "history.jsonl")
        report = history.compare(report)
        DashboardWriter().write(report, output)
        history.append(report)
        print(json.dumps(report.to_dict(), indent=2) if output_format == "json" else DashboardTextRenderer().render(report))
        if output_format == "text":
            print(f"Dashboard: {output / 'dashboard.html'}")
        return 0 if report.passed else 1
