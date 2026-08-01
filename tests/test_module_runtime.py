"""Tests for the M16 dependency-aware module runtime."""

from __future__ import annotations

import pytest

from src.modules import (
    BaseModule,
    ModuleAlreadyRegisteredError,
    ModuleCycleError,
    ModuleDependencyError,
    ModuleRegistry,
    ModuleRuntime,
    ModuleRuntimeState,
    ModuleStartupError,
)


class RecordingModule(BaseModule):
    def __init__(
        self,
        name: str,
        calls: list[str],
        dependencies: tuple[str, ...] = (),
        *,
        fail_start: bool = False,
    ) -> None:
        self.name = name
        self.dependencies = dependencies
        self.calls = calls
        self.fail_start = fail_start

    def configure(self, container: object) -> None:
        self.calls.append(f"configure:{self.name}:{container}")

    def start(self, context: object) -> None:
        self.calls.append(f"start:{self.name}:{context}")
        if self.fail_start:
            raise RuntimeError("boom")

    def stop(self, context: object) -> None:
        self.calls.append(f"stop:{self.name}:{context}")


def test_registry_rejects_blank_name() -> None:
    with pytest.raises(ValueError):
        ModuleRegistry().register(RecordingModule(" ", []))


def test_registry_rejects_duplicate_name() -> None:
    registry = ModuleRegistry()
    registry.register(RecordingModule("core", []))
    with pytest.raises(ModuleAlreadyRegisteredError):
        registry.register(RecordingModule("core", []))


def test_registry_rejects_unknown_dependency_when_planning() -> None:
    registry = ModuleRegistry()
    registry.register(RecordingModule("api", [], ("core",)))
    with pytest.raises(ModuleDependencyError):
        registry.plan()


def test_registry_detects_dependency_cycle() -> None:
    registry = ModuleRegistry()
    registry.register(RecordingModule("one", [], ("two",)))
    registry.register(RecordingModule("two", [], ("one",)))
    with pytest.raises(ModuleCycleError):
        registry.plan()


def test_registry_plans_dependencies_before_dependents_stably() -> None:
    registry = ModuleRegistry()
    registry.register(RecordingModule("api", [], ("core",)))
    registry.register(RecordingModule("core", []))
    registry.register(RecordingModule("reporting", [], ("core",)))
    assert tuple(module.name for module in registry.plan()) == (
        "core",
        "api",
        "reporting",
    )


def test_runtime_configures_starts_and_stops_in_safe_order() -> None:
    calls: list[str] = []
    registry = ModuleRegistry()
    registry.register(RecordingModule("api", calls, ("core",)))
    registry.register(RecordingModule("core", calls))
    runtime = ModuleRuntime(registry)
    runtime.configure("container")
    assert runtime.plan == ("core", "api")
    assert runtime.state is ModuleRuntimeState.CONFIGURED
    runtime.start("context")
    assert runtime.state is ModuleRuntimeState.RUNNING
    runtime.stop("context")
    assert runtime.state is ModuleRuntimeState.STOPPED
    assert calls == [
        "configure:core:container",
        "configure:api:container",
        "start:core:context",
        "start:api:context",
        "stop:api:context",
        "stop:core:context",
    ]


def test_runtime_requires_configuration_before_start() -> None:
    with pytest.raises(RuntimeError):
        ModuleRuntime().start("context")


def test_runtime_can_only_be_configured_once() -> None:
    runtime = ModuleRuntime()
    runtime.configure("container")
    with pytest.raises(RuntimeError):
        runtime.configure("container")


def test_runtime_rolls_back_started_modules_on_failure() -> None:
    calls: list[str] = []
    registry = ModuleRegistry()
    registry.register(RecordingModule("core", calls))
    registry.register(RecordingModule("api", calls, ("core",), fail_start=True))
    runtime = ModuleRuntime(registry)
    runtime.configure("container")
    with pytest.raises(ModuleStartupError):
        runtime.start("context")
    assert runtime.state is ModuleRuntimeState.FAILED
    assert calls[-1] == "stop:core:context"


def test_runtime_reports_shutdown_failures_after_stopping_all() -> None:
    calls: list[str] = []

    class BrokenStop(RecordingModule):
        def stop(self, context: object) -> None:
            super().stop(context)
            raise RuntimeError("stop failed")

    registry = ModuleRegistry()
    registry.register(BrokenStop("core", calls))
    runtime = ModuleRuntime(registry)
    runtime.configure("container")
    runtime.start("context")
    with pytest.raises(RuntimeError, match="stop failed"):
        runtime.stop("context")
    assert runtime.state is ModuleRuntimeState.STOPPED
