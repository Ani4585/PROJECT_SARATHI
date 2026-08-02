"""Tests for the official M24 dynamic registration framework."""

from __future__ import annotations

from argparse import Namespace

import pytest

from scripts.tooling.cli.command import Command
from scripts.tooling.cli.context import CommandContext
from scripts.tooling.cli.registry import CommandRegistry
from src.container import ServiceContainer
from src.extensions import ExtensionPoint, ExtensionPolicy, ExtensionRegistry
from src.hooks import HookEvent, HookRegistry
from src.plugins import (
    DynamicRegistrationError,
    DynamicRegistrationManager,
    LateRegistrationError,
    Plugin,
    PluginContext,
    PluginManifest,
    PluginRegistry,
    PluginState,
    RegistrationKind,
    RegistrationState,
)


class GreetingService:
    def greet(self) -> str:
        return "hello"


class Formatter:
    def format(self, value: str) -> str:
        return value.upper()


class DemoCommand(Command):
    @property
    def name(self) -> str:
        return "demo-plugin"

    @property
    def description(self) -> str:
        return "Exercise the integration plugin."

    def execute(self, context: CommandContext, arguments: Namespace) -> int:
        del context, arguments
        return 0


def create_manager() -> tuple[
    DynamicRegistrationManager,
    ServiceContainer,
    CommandRegistry,
    HookRegistry,
    ExtensionRegistry,
]:
    services = ServiceContainer()
    commands = CommandRegistry()
    hooks = HookRegistry()
    extensions = ExtensionRegistry()
    extensions.define(ExtensionPoint("formatter", Formatter, ExtensionPolicy.COMPOSE))
    return (
        DynamicRegistrationManager(
            services,
            commands=commands,
            hooks=hooks,
            extensions=extensions,
        ),
        services,
        commands,
        hooks,
        extensions,
    )


def test_conditional_registration_skips_without_ownership_record() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    scope = manager.open_scope("conditional")
    assert scope.register_service("disabled", object(), condition=False) is False
    assert scope.register_command(DemoCommand(), condition=lambda: False) is False
    assert services.has("disabled") is False
    assert commands.contains("demo-plugin") is False
    assert scope.records == ()
    with pytest.raises(TypeError, match="must produce a boolean"):
        scope.register_service("invalid", object(), condition=lambda: "yes")  # type: ignore[arg-type]


def test_named_factory_and_typed_services_are_owned_and_removed() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    scope = manager.open_scope("services")
    instance = GreetingService()
    scope.register_service("greeting", instance)
    scope.register_factory("created", lambda: {"created": True})
    scope.register_typed_service(GreetingService, instance)
    assert services.resolve("greeting") is instance
    assert services.resolve("created") == {"created": True}
    assert services.resolve_type(GreetingService) is instance
    assert tuple(record.kind for record in scope.records) == (
        RegistrationKind.SERVICE,
        RegistrationKind.SERVICE,
        RegistrationKind.TYPED_SERVICE,
    )
    report = manager.unload("services")
    assert report.passed is True
    assert services.has("greeting") is False
    assert services.has("created") is False
    assert services.has_type(GreetingService) is False


def test_plugin_cannot_overwrite_existing_typed_framework_service() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    original = GreetingService()
    services.register_type(GreetingService, original)
    scope = manager.open_scope("unsafe")
    with pytest.raises(Exception, match="already registered"):
        scope.register_typed_service(GreetingService, GreetingService())
    assert services.resolve_type(GreetingService) is original
    assert scope.records == ()


def test_freeze_prevents_unsafe_late_mutation() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    scope = manager.open_scope("frozen")
    scope.freeze()
    assert scope.state is RegistrationState.FROZEN
    with pytest.raises(LateRegistrationError, match="is frozen"):
        scope.register_service("late", object())
    manager.unload("frozen")
    with pytest.raises(LateRegistrationError, match="is closed"):
        scope.add_cleanup("late", lambda: None)


def test_commands_hooks_and_extensions_are_removed_by_owner() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    calls: list[str] = []
    formatter = Formatter()
    scope = manager.open_scope("contributor")
    scope.register_command(DemoCommand())
    scope.register_hook("after.start", lambda event: calls.append("hook"))
    scope.register_extension("formatter", formatter, priority=10)
    assert commands.contains("demo-plugin") is True
    hooks.dispatch(HookEvent("after.start", {}))
    assert calls == ["hook"]
    assert extensions.resolve("formatter") == (formatter,)
    manager.unload("contributor")
    assert commands.contains("demo-plugin") is False
    assert hooks.registrations("after.start") == ()
    assert extensions.resolve("formatter") == ()


def test_unloading_one_owner_preserves_another_owner() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    first = manager.open_scope("first")
    second = manager.open_scope("second")
    first.register_service("first-service", object())
    second.register_service("second-service", object())
    manager.unload("first")
    assert services.has("first-service") is False
    assert services.has("second-service") is True
    assert manager.has_scope("second") is True


def test_cleanup_is_reverse_ordered_and_failure_isolated() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    calls: list[str] = []
    scope = manager.open_scope("cleanup")
    scope.add_cleanup("first", lambda: calls.append("first"))

    def broken() -> None:
        calls.append("broken")
        raise RuntimeError("cleanup failed")

    scope.add_cleanup("broken", broken)
    scope.add_cleanup("last", lambda: calls.append("last"))
    report = manager.unload("cleanup")
    assert calls == ["last", "broken", "first"]
    assert report.passed is False
    assert len(report.failures) == 1
    assert report.failures[0].record.key == "broken"
    assert "RuntimeError: cleanup failed" in report.failures[0].message


def test_manager_rejects_duplicate_owner_and_unloads_all_in_reverse() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    calls: list[str] = []
    first = manager.open_scope("first")
    second = manager.open_scope("second")
    first.add_cleanup("first", lambda: calls.append("first"))
    second.add_cleanup("second", lambda: calls.append("second"))
    with pytest.raises(DynamicRegistrationError, match="already exists"):
        manager.open_scope("first")
    reports = manager.unload_all()
    assert tuple(report.owner for report in reports) == ("second", "first")
    assert calls == ["second", "first"]


class IntegratedPlugin(Plugin):
    def __init__(self, calls: list[str], *, fail_register: bool = False, fail_stop: bool = False) -> None:
        self.calls = calls
        self.fail_register = fail_register
        self.fail_stop = fail_stop

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest("integration", "1.0.0", "Full integration plugin")

    def register(self, registrations) -> None:
        registrations.register_service("plugin.greeting", GreetingService())
        if self.fail_register:
            raise RuntimeError("registration failed")
        registrations.register_typed_service(GreetingService, GreetingService())
        registrations.register_command(DemoCommand())
        registrations.register_hook("plugin.started", lambda event: self.calls.append("hook"))
        registrations.register_extension("formatter", Formatter(), priority=10)

    def configure(self, context: PluginContext) -> None:
        self.calls.append("configure")

    def start(self, context: PluginContext) -> None:
        self.calls.append("start")

    def stop(self, context: PluginContext) -> None:
        self.calls.append("stop")
        if self.fail_stop:
            raise RuntimeError("stop failed")


def test_full_plugin_integration_registers_freezes_and_unloads() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    calls: list[str] = []
    plugins = PluginRegistry()
    plugins.register(IntegratedPlugin(calls))
    context = PluginContext("0.8.11", {}, frozenset())
    started = plugins.start_all(context, registration_manager=manager)
    assert started.passed is True
    assert manager.scope("integration").state is RegistrationState.FROZEN
    assert services.resolve("plugin.greeting").greet() == "hello"
    assert services.has_type(GreetingService) is True
    assert commands.contains("demo-plugin") is True
    hooks.dispatch(HookEvent("plugin.started", {}))
    assert calls == ["configure", "start", "hook"]
    assert len(extensions.resolve("formatter")) == 1  # type: ignore[arg-type]

    stopped = plugins.stop_all(context)
    assert stopped.passed is True
    assert plugins.state("integration") is PluginState.STOPPED
    assert manager.has_scope("integration") is False
    assert services.has("plugin.greeting") is False
    assert services.has_type(GreetingService) is False
    assert commands.contains("demo-plugin") is False
    assert hooks.registrations("plugin.started") == ()
    assert extensions.resolve("formatter") == ()


def test_registration_failure_rolls_back_partial_contributions() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    plugins = PluginRegistry()
    plugins.register(IntegratedPlugin([], fail_register=True))
    report = plugins.start_all(
        PluginContext("0.8.11", {}, frozenset()),
        registration_manager=manager,
    )
    assert report.failures == 1
    assert "RuntimeError: registration failed" in (report.operations[0].message or "")
    assert services.has("plugin.greeting") is False
    assert manager.has_scope("integration") is False


def test_stop_failure_still_unloads_all_contributions() -> None:
    manager, services, commands, hooks, extensions = create_manager()
    plugins = PluginRegistry()
    plugins.register(IntegratedPlugin([], fail_stop=True))
    context = PluginContext("0.8.11", {}, frozenset())
    plugins.start_all(context, registration_manager=manager)
    report = plugins.stop_all(context)
    assert report.failures == 1
    assert "RuntimeError: stop failed" in report.operations[0].message
    assert services.has("plugin.greeting") is False
    assert commands.contains("demo-plugin") is False
    assert manager.has_scope("integration") is False


def test_complete_plugin_example_runs_and_cleans_up() -> None:
    from examples.plugins.integrated_plugin import run_example

    assert run_example() == {
        "started": True,
        "greeting": "Hello, SARATHI!",
        "formatted": "HELLO, SARATHI!",
        "command_available": True,
        "hook_calls": ("ready",),
        "stopped": True,
        "clean_after_unload": True,
    }
