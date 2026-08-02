"""Safe-share runtime diagnostic bundle command."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path

from config.settings import settings
from src.container import ServiceContainer
from src.runtime_diagnostics import (
    DiagnosticBundleJsonRenderer,
    DiagnosticBundleTextRenderer,
    DiagnosticBundleWriter,
    RuntimeDiagnosticCollector,
)

from ...console import print_header
from ..command import Command
from ..context import CommandContext


class DiagnosticsCommand(Command):
    @property
    def name(self) -> str:
        return "diagnostics"

    @property
    def description(self) -> str:
        return "Generate a redacted runtime diagnostic bundle."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("--format", choices=("text", "json"), default="text")
        parser.add_argument(
            "--output",
            type=Path,
            default=Path("reports/diagnostics/runtime-diagnostics.json"),
        )

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        output_format = getattr(arguments, "format", "text")
        if output_format == "text":
            print_header("CLI - DIAGNOSTICS")
        bundle = RuntimeDiagnosticCollector().collect(configuration=settings, container=ServiceContainer())
        output_argument = getattr(arguments, "output", Path("reports/diagnostics/runtime-diagnostics.json"))
        output = output_argument if output_argument.is_absolute() else context.project_root / output_argument
        DiagnosticBundleWriter().write_json(bundle, output)
        renderer = DiagnosticBundleJsonRenderer() if output_format == "json" else DiagnosticBundleTextRenderer()
        print(renderer.render(bundle))
        if output_format == "text":
            print(f"Bundle: {output}")
        return 0 if bundle.failures == 0 else 1
