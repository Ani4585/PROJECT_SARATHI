"""CLI extension diagnostic command."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace

from scripts.tooling.cli.plugins import (
    CliPluginJsonRenderer,
    CliPluginLoader,
    CliPluginTextRenderer,
)

from ...console import print_header
from ..command import Command
from ..context import CommandContext


class PluginsCommand(Command):
    """Display installed CLI extension discovery results."""

    def __init__(self, loader: CliPluginLoader) -> None:
        self._loader = loader

    @property
    def name(self) -> str:
        return "plugins"

    @property
    def description(self) -> str:
        return "Inspect installed CLI command extensions."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("--format", choices=("text", "json"), default="text")

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        del context
        output_format = getattr(arguments, "format", "text")
        if output_format == "text":
            print_header("CLI - PLUGINS")
        report = self._loader.last_report
        renderer = CliPluginJsonRenderer() if output_format == "json" else CliPluginTextRenderer()
        print(renderer.render(report))
        return 0 if report.passed else 1
