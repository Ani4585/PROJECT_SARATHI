"""Operational health-monitoring CLI command."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace

from src.health import (
    HealthGroup,
    HealthJsonRenderer,
    HealthRunner,
    HealthTextRenderer,
    create_default_health_registry,
)

from ...console import print_header
from ..command import Command
from ..context import CommandContext


class MonitorCommand(Command):
    @property
    def name(self) -> str:
        return "monitor"

    @property
    def description(self) -> str:
        return "Run grouped operational health checks."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--group",
            choices=("all", *(group.value for group in HealthGroup)),
            default="all",
        )
        parser.add_argument("--format", choices=("text", "json"), default="text")

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        output_format = getattr(arguments, "format", "text")
        if output_format == "text":
            print_header("CLI - MONITOR")
        selected = getattr(arguments, "group", "all")
        groups = None if selected == "all" else (HealthGroup(selected),)
        report = HealthRunner(create_default_health_registry(context.project_root)).run(groups)
        renderer = HealthJsonRenderer() if output_format == "json" else HealthTextRenderer()
        print(renderer.render(report))
        return 0 if report.passed else 1
