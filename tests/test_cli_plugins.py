"""Tests for official M12.7 CLI extension discovery."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts.tooling.cli.command import Command
from scripts.tooling.cli.commands.builtins import create_builtin_registry
from scripts.tooling.cli.commands.plugins import PluginsCommand
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.cli.plugins import (
    CLI_ENTRY_POINT_GROUP,
    CliPluginJsonRenderer,
    CliPluginLoader,
    CliPluginStatus,
    CliPluginTextRenderer,
)
from scripts.tooling.cli.registry import CommandRegistry


class ExampleCommand(Command):
    @property
    def name(self) -> str:
        return "example"

    @property
    def description(self) -> str:
        return "Example extension."

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        del context, arguments
        return 0


class FakeEntryPoint:
    def __init__(self, name: str, value: str, target: object) -> None:
        self.name = name
        self.value = value
        self._target = target

    def load(self) -> object:
        if isinstance(self._target, BaseException):
            raise self._target
        return self._target


def test_loader_registers_command_instance() -> None:
    registry = CommandRegistry()
    loader = CliPluginLoader(lambda: (FakeEntryPoint("example", "package:command", ExampleCommand()),))
    report = loader.load_into(registry)
    assert registry.contains("example") is True
    assert report.loaded == 1
    assert report.failed == 0


def test_loader_accepts_command_class_and_factory() -> None:
    class FactoryCommand(ExampleCommand):
        @property
        def name(self) -> str:
            return "factory"

    registry = CommandRegistry()
    loader = CliPluginLoader(
        lambda: (
            FakeEntryPoint("class", "package:ExampleCommand", ExampleCommand),
            FakeEntryPoint("factory", "package:create", lambda: FactoryCommand()),
        )
    )
    report = loader.load_into(registry)
    assert registry.names() == ("example", "factory")
    assert report.loaded == 2


def test_loader_isolates_broken_and_invalid_extensions() -> None:
    registry = CommandRegistry()
    loader = CliPluginLoader(
        lambda: (
            FakeEntryPoint("broken", "package:broken", RuntimeError("boom")),
            FakeEntryPoint("invalid", "package:value", object()),
        )
    )
    report = loader.load_into(registry)
    assert report.failed == 2
    assert report.passed is False
    assert "RuntimeError: boom" in (report.diagnostics[0].message or "")


def test_loader_reports_duplicate_builtin_without_replacing_it() -> None:
    registry = CommandRegistry()
    registry.register(ExampleCommand())
    loader = CliPluginLoader(lambda: (FakeEntryPoint("duplicate", "package:command", ExampleCommand()),))
    report = loader.load_into(registry)
    assert registry.names() == ("example",)
    assert report.failed == 1
    assert "CommandAlreadyRegisteredError" in (report.diagnostics[0].message or "")


def test_loader_orders_entry_points_deterministically() -> None:
    class AlphaCommand(ExampleCommand):
        @property
        def name(self) -> str:
            return "alpha"

    loader = CliPluginLoader(
        lambda: (
            FakeEntryPoint("zeta", "package:zeta", ExampleCommand()),
            FakeEntryPoint("alpha", "package:alpha", AlphaCommand()),
        )
    )
    report = loader.load_into(CommandRegistry())
    assert tuple(item.entry_point for item in report.diagnostics) == ("alpha", "zeta")


def test_loader_isolates_discovery_failure() -> None:
    def broken_discovery():
        raise OSError("metadata unavailable")

    report = CliPluginLoader(broken_discovery).load_into(CommandRegistry())
    assert report.failed == 1
    assert report.diagnostics[0].entry_point == "<discovery>"


def test_plugin_renderers_expose_group_and_results() -> None:
    loader = CliPluginLoader(lambda: (FakeEntryPoint("example", "package:command", ExampleCommand()),))
    report = loader.load_into(CommandRegistry())
    assert "[LOADED] example" in CliPluginTextRenderer().render(report)
    document = json.loads(CliPluginJsonRenderer().render(report))
    assert document["group"] == CLI_ENTRY_POINT_GROUP
    assert document["summary"]["loaded"] == 1


def test_builtin_registry_loads_injected_extension() -> None:
    loader = CliPluginLoader(lambda: (FakeEntryPoint("example", "package:command", ExampleCommand()),))
    registry = create_builtin_registry(loader)
    assert registry.contains("example") is True
    assert registry.contains("plugins") is True


def test_plugins_command_returns_failure_for_broken_extension(
    tmp_path: Path,
    capsys,
) -> None:
    loader = CliPluginLoader(lambda: (FakeEntryPoint("broken", "package:broken", RuntimeError("boom")),))
    loader.load_into(CommandRegistry())
    exit_code = PluginsCommand(loader).execute(
        CommandContext(tmp_path, "python"),
        Namespace(format="json"),
    )
    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["summary"]["failed"] == 1
