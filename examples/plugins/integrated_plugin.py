"""Complete M24 plugin contribution and unload example."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tooling.cli.command import Command
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.cli.registry import CommandRegistry
from src.container import ServiceContainer
from src.core.version import VERSION
from src.extensions import ExtensionPoint, ExtensionPolicy, ExtensionRegistry
from src.hooks import HookEvent, HookRegistry
from src.plugins import (
    DynamicRegistrationManager,
    Plugin,
    PluginContext,
    PluginManifest,
    PluginRegistry,
)


class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


class GreetingFormatter:
    def format(self, value: str) -> str:
        return value.upper()


class GreetingCommand(Command):
    @property
    def name(self) -> str:
        return "plugin-greeting"

    @property
    def description(self) -> str:
        return "Print a greeting supplied by the example plugin."

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        del context, arguments
        return 0


class GreetingPlugin(Plugin):
    def __init__(self, hook_calls: list[str]) -> None:
        self._hook_calls = hook_calls

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            "greeting-example",
            "1.0.0",
            "Demonstrate every M24 contribution type.",
        )

    def register(self, registrations) -> None:
        registrations.register_service("greeting", GreetingService())
        registrations.register_command(GreetingCommand())
        registrations.register_hook(
            "application.ready",
            lambda event: self._hook_calls.append(str(event.payload["state"])),
        )
        registrations.register_extension(
            "greeting.formatter",
            GreetingFormatter(),
            priority=10,
        )


def run_example() -> dict[str, object]:
    services = ServiceContainer()
    commands = CommandRegistry()
    hooks = HookRegistry()
    extensions = ExtensionRegistry()
    extensions.define(
        ExtensionPoint(
            "greeting.formatter",
            GreetingFormatter,
            ExtensionPolicy.COMPOSE,
        )
    )
    registrations = DynamicRegistrationManager(
        services,
        commands=commands,
        hooks=hooks,
        extensions=extensions,
    )
    hook_calls: list[str] = []
    plugins = PluginRegistry()
    plugins.register(GreetingPlugin(hook_calls))
    context = PluginContext(VERSION, {"environment": "example"}, frozenset())

    started = plugins.start_all(context, registration_manager=registrations)
    greeting = services.resolve("greeting").greet("SARATHI")
    hooks.dispatch(HookEvent("application.ready", {"state": "ready"}))
    formatters = extensions.resolve("greeting.formatter")
    formatted = formatters[0].format(greeting)  # type: ignore[index]
    command_available = commands.contains("plugin-greeting")
    stopped = plugins.stop_all(context)

    clean = (
        not services.has("greeting")
        and not commands.contains("plugin-greeting")
        and not hooks.registrations("application.ready")
        and extensions.resolve("greeting.formatter") == ()
    )
    return {
        "started": started.passed,
        "greeting": greeting,
        "formatted": formatted,
        "command_available": command_available,
        "hook_calls": tuple(hook_calls),
        "stopped": stopped.passed,
        "clean_after_unload": clean,
    }


if __name__ == "__main__":
    result = run_example()
    for key, value in result.items():
        print(f"{key}: {value}")
