"""Installed developer-CLI extension discovery and diagnostics."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from typing import Protocol

from .command import Command
from .registry import CommandRegistry


CLI_ENTRY_POINT_GROUP = "project_sarathi.cli"


class CliEntryPoint(Protocol):
    """Describe the entry-point surface required by the loader."""

    name: str
    value: str

    def load(self) -> object: ...


class CliPluginStatus(StrEnum):
    """Describe one CLI extension discovery outcome."""

    LOADED = "loaded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CliPluginDiagnostic:
    """Record one isolated CLI plugin loading result."""

    entry_point: str
    target: str
    status: CliPluginStatus
    command: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "entry_point": self.entry_point,
            "target": self.target,
            "status": self.status.value,
            "command": self.command,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class CliPluginReport:
    """Aggregate deterministic CLI plugin diagnostics."""

    diagnostics: tuple[CliPluginDiagnostic, ...] = ()

    @property
    def loaded(self) -> int:
        return sum(item.status is CliPluginStatus.LOADED for item in self.diagnostics)

    @property
    def failed(self) -> int:
        return sum(item.status is CliPluginStatus.FAILED for item in self.diagnostics)

    @property
    def passed(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict[str, object]:
        return {
            "title": "PROJECT SARATHI CLI Plugin Report",
            "group": CLI_ENTRY_POINT_GROUP,
            "summary": {
                "passed": self.passed,
                "discovered": len(self.diagnostics),
                "loaded": self.loaded,
                "failed": self.failed,
            },
            "plugins": [item.to_dict() for item in self.diagnostics],
        }


def _default_entry_points() -> Iterable[CliEntryPoint]:
    discovered = metadata.entry_points()
    if hasattr(discovered, "select"):
        return discovered.select(group=CLI_ENTRY_POINT_GROUP)
    return tuple(item for item in discovered if item.group == CLI_ENTRY_POINT_GROUP)


def _resolve_command(candidate: object) -> Command:
    if isinstance(candidate, Command):
        return candidate
    if isinstance(candidate, type) and issubclass(candidate, Command):
        return candidate()
    if callable(candidate):
        resolved = candidate()
        if isinstance(resolved, Command):
            return resolved
    raise TypeError("CLI entry point must expose a Command instance, Command class, or zero-argument Command factory.")


class CliPluginLoader:
    """Discover and safely register installed CLI command extensions."""

    def __init__(self, entry_points: Callable[[], Iterable[CliEntryPoint]] = _default_entry_points) -> None:
        self._entry_points = entry_points
        self._last_report = CliPluginReport()

    @property
    def last_report(self) -> CliPluginReport:
        return self._last_report

    def load_into(self, registry: CommandRegistry) -> CliPluginReport:
        diagnostics: list[CliPluginDiagnostic] = []
        try:
            entries = tuple(sorted(self._entry_points(), key=lambda item: (item.name, item.value)))
        except Exception as error:
            self._last_report = CliPluginReport(
                (
                    CliPluginDiagnostic(
                        "<discovery>",
                        CLI_ENTRY_POINT_GROUP,
                        CliPluginStatus.FAILED,
                        message=f"{type(error).__name__}: {error}",
                    ),
                )
            )
            return self._last_report
        for entry in entries:
            try:
                command = _resolve_command(entry.load())
                registry.register(command)
                diagnostics.append(
                    CliPluginDiagnostic(
                        entry.name,
                        entry.value,
                        CliPluginStatus.LOADED,
                        command=command.name,
                    )
                )
            except Exception as error:
                diagnostics.append(
                    CliPluginDiagnostic(
                        entry.name,
                        entry.value,
                        CliPluginStatus.FAILED,
                        message=f"{type(error).__name__}: {error}",
                    )
                )
        self._last_report = CliPluginReport(tuple(diagnostics))
        return self._last_report


class CliPluginTextRenderer:
    """Render CLI plugin diagnostics for people."""

    def render(self, report: CliPluginReport) -> str:
        lines = ["PROJECT SARATHI CLI Plugin Report", "=" * 33]
        if not report.diagnostics:
            lines.append("No installed CLI extensions were discovered.")
        for item in report.diagnostics:
            lines.append(f"[{item.status.value.upper()}] {item.entry_point} -> {item.target}")
            if item.command:
                lines.append(f"  Command: {item.command}")
            if item.message:
                lines.append(f"  {item.message}")
        lines.extend(
            (
                "",
                f"Summary: {len(report.diagnostics)} discovered | {report.loaded} loaded | {report.failed} failed",
                "Overall: PASS" if report.passed else "Overall: FAIL",
            )
        )
        return "\n".join(lines)


class CliPluginJsonRenderer:
    """Render CLI plugin diagnostics for automation."""

    def render(self, report: CliPluginReport) -> str:
        return json.dumps(report.to_dict(), indent=2)
