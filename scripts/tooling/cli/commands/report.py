"""Developer report CLI command."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path

from scripts.tooling.developer_report import (
    DeveloperReportCollector,
    DeveloperReportJsonRenderer,
    DeveloperReportTextRenderer,
    DeveloperReportWriter,
)

from ...console import print_header
from ..command import Command
from ..context import CommandContext


class ReportCommand(Command):
    """Generate dependency, environment, and tooling reports."""

    @property
    def name(self) -> str:
        return "report"

    @property
    def description(self) -> str:
        return "Generate dependency, environment, and tooling reports."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument(
            "--output",
            type=Path,
            default=Path("reports/developer"),
            help="Directory for JSON and HTML report files.",
        )

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        output_format = getattr(arguments, "format", "text")
        if output_format == "text":
            print_header("CLI - REPORT")
        report = DeveloperReportCollector().collect(context.project_root)
        output_argument = getattr(arguments, "output", Path("reports/developer"))
        output = output_argument if output_argument.is_absolute() else context.project_root / output_argument
        json_path, html_path = DeveloperReportWriter().write(report, output)
        renderer = DeveloperReportJsonRenderer() if output_format == "json" else DeveloperReportTextRenderer()
        print(renderer.render(report))
        if output_format == "text":
            print(f"JSON report: {json_path}")
            print(f"HTML report: {html_path}")
        return 0 if report.passed else 1
