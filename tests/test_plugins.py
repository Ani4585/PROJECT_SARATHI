"""Tests for the official M19 plugin system foundation."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from src.plugins import (
    Plugin,
    PluginContext,
    PluginManifest,
    PluginRegistry,
    PluginState,
)


@dataclass
class RecordingPlugin(Plugin):
    name: str
    calls: list[str]
    version: str = "1.0.0"
    minimum: str = "0.0.0"
    maximum: str | None = None
    required: frozenset[str] = frozenset()
    provided: frozenset[str] = frozenset()
    enabled_by_default: bool = True
    fail_on: str | None = None
    contexts: list[PluginContext] = field(default_factory=list)

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=self.name,
            version=self.version,
            description=f"Plugin {self.name}",
            minimum_framework_version=self.minimum,
            maximum_framework_version=self.maximum,
            required_capabilities=self.required,
            provided_capabilities=self.provided,
            enabled_by_default=self.enabled_by_default,
        )

    def configure(self, context: PluginContext) -> None:
        self.calls.append(f"configure:{self.name}")
        self.contexts.append(context)
        if self.fail_on == "configure":
            raise RuntimeError("configure failed")

    def start(self, context: PluginContext) -> None:
        self.calls.append(f"start:{self.name}")
        if self.fail_on == "start":
            raise RuntimeError("start failed")

    def stop(self, context: PluginContext) -> None:
        del context
        self.calls.append(f"stop:{self.name}")
        if self.fail_on == "stop":
            raise RuntimeError("stop failed")


def context(*capabilities: str) -> PluginContext:
    return PluginContext("0.8.6", {"mode": "test"}, frozenset(capabilities))


def test_manifest_normalizes_metadata_and_validates_versions() -> None:
    manifest = PluginManifest(
        name=" sample ",
        version="2.1.0",
        description=" Sample plugin ",
        required_capabilities=frozenset({" storage "}),
    )
    assert manifest.name == "sample"
    assert manifest.description == "Sample plugin"
    assert manifest.required_capabilities == frozenset({"storage"})
    with pytest.raises(ValueError, match="Invalid semantic version"):
        PluginManifest("bad", "release", "Bad version")
    with pytest.raises(ValueError, match="must not precede"):
        PluginManifest(
            "bad-range",
            "1.0.0",
            "Bad range",
            minimum_framework_version="2.0.0",
            maximum_framework_version="1.0.0",
        )


def test_registry_rejects_invalid_and_duplicate_plugins() -> None:
    registry = PluginRegistry()
    with pytest.raises(TypeError, match="implement Plugin"):
        registry.register(object())  # type: ignore[arg-type]
    registry.register(RecordingPlugin("alpha", []))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(RecordingPlugin("alpha", []))


def test_registry_validates_framework_compatibility_and_capabilities() -> None:
    registry = PluginRegistry()
    registry.register(RecordingPlugin("future", [], minimum="1.0.0"))
    registry.register(RecordingPlugin("legacy", [], maximum="0.7.0"))
    registry.register(RecordingPlugin("consumer", [], required=frozenset({"storage"})))
    assert registry.validate("0.8.6") == (
        "consumer: missing capabilities storage",
        "future: requires framework >= 1.0.0",
        "legacy: requires framework <= 0.7.0",
    )


def test_enabled_provider_supplies_capability_to_plugin_context() -> None:
    registry = PluginRegistry()
    provider = RecordingPlugin("provider", [], provided=frozenset({"storage"}))
    consumer = RecordingPlugin("consumer", [], required=frozenset({"storage"}))
    registry.register(provider)
    registry.register(consumer)
    report = registry.start_all(context("logging"))
    assert report.passed is True
    assert consumer.contexts[0].capabilities == frozenset({"logging", "storage"})


def test_disabled_provider_does_not_satisfy_required_capability() -> None:
    registry = PluginRegistry()
    registry.register(RecordingPlugin("provider", [], provided=frozenset({"storage"})))
    registry.register(RecordingPlugin("consumer", [], required=frozenset({"storage"})))
    report = registry.start_all(context(), enabled={"provider": False})
    assert report.find("provider").state is PluginState.DISABLED  # type: ignore[union-attr]
    assert report.find("consumer").state is PluginState.FAILED  # type: ignore[union-attr]


def test_default_and_explicit_enable_policies_are_honored() -> None:
    registry = PluginRegistry()
    registry.register(RecordingPlugin("off", [], enabled_by_default=False))
    registry.register(RecordingPlugin("on", []))
    first = registry.start_all(context())
    assert tuple(item.state for item in first.operations) == (
        PluginState.DISABLED,
        PluginState.STARTED,
    )
    second = registry.start_all(context(), enabled={"off": True, "on": False})
    assert tuple(item.state for item in second.operations) == (
        PluginState.STARTED,
        PluginState.DISABLED,
    )


def test_multiple_plugins_start_deterministically_and_isolate_failures() -> None:
    calls: list[str] = []
    registry = PluginRegistry()
    registry.register(RecordingPlugin("zulu", calls))
    registry.register(RecordingPlugin("broken", calls, fail_on="start"))
    registry.register(RecordingPlugin("alpha", calls))
    report = registry.start_all(context())
    assert calls == [
        "configure:alpha",
        "start:alpha",
        "configure:broken",
        "start:broken",
        "configure:zulu",
        "start:zulu",
    ]
    assert report.failures == 1
    assert registry.state("alpha") is PluginState.STARTED
    assert registry.state("broken") is PluginState.FAILED
    assert registry.state("zulu") is PluginState.STARTED


def test_plugins_stop_in_reverse_order_and_isolate_failures() -> None:
    calls: list[str] = []
    registry = PluginRegistry()
    registry.register(RecordingPlugin("alpha", calls))
    registry.register(RecordingPlugin("middle", calls, fail_on="stop"))
    registry.register(RecordingPlugin("zulu", calls))
    registry.start_all(context())
    calls.clear()
    report = registry.stop_all(context())
    assert calls == ["stop:zulu", "stop:middle", "stop:alpha"]
    assert report.failures == 1
    assert registry.state("zulu") is PluginState.STOPPED
    assert registry.state("middle") is PluginState.FAILED
    assert registry.state("alpha") is PluginState.STOPPED


def test_plugin_context_configuration_is_immutable() -> None:
    plugin_context = context()
    with pytest.raises(TypeError):
        plugin_context.configuration["mode"] = "changed"  # type: ignore[index]
