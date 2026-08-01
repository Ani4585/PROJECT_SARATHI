"""Repository Audit CLI command."""

from __future__ import annotations

from argparse import Namespace
from typing import Protocol

from scripts.tooling.audit import AuditReport, AuditReportRenderer, create_repository_auditor

from ...console import print_header
from ..command import Command
from ..context import CommandContext


class _AuditRunner(Protocol):
    def run(self, project_root: object) -> AuditReport: ...


class _AuditRenderer(Protocol):
    def render(self, report: AuditReport) -> str: ...


class AuditCommand(Command):
    """Execute and display a repository audit."""

    def __init__(self, auditor: _AuditRunner | None = None, renderer: _AuditRenderer | None = None) -> None:
        self._auditor = auditor if auditor is not None else create_repository_auditor()
        self._renderer = renderer if renderer is not None else AuditReportRenderer()

    @property
    def name(self) -> str:
        return "audit"

    @property
    def description(self) -> str:
        return "Audit repository structure and integrity."

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        del arguments
        print_header("CLI - AUDIT")
        report = self._auditor.run(context.project_root)
        print(self._renderer.render(report))
        return 0 if report.passed else 1
