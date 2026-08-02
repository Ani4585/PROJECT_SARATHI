"""Tests for official M21 plugin package discovery."""

from __future__ import annotations

import json
from pathlib import Path

from src.plugins import DiscoveryStatus, Plugin, PluginDiscovery, PluginManifest


class ExamplePlugin(Plugin):
    def __init__(
        self,
        name: str = "example",
        *,
        minimum: str = "0.0.0",
        required: frozenset[str] = frozenset(),
    ) -> None:
        self._manifest = PluginManifest(
            name,
            "1.0.0",
            f"Plugin {name}",
            minimum_framework_version=minimum,
            required_capabilities=required,
        )

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest


class FakeEntryPoint:
    def __init__(self, name: str, target: object) -> None:
        self.name = name
        self.value = f"package:{name}"
        self.target = target

    def load(self) -> object:
        if isinstance(self.target, Exception):
            raise self.target
        return self.target


def test_discovers_entry_point_instance_class_and_factory() -> None:
    discovery = PluginDiscovery(
        entry_points=lambda: (
            FakeEntryPoint("instance", ExamplePlugin("instance")),
            FakeEntryPoint("class", ExamplePlugin),
            FakeEntryPoint("factory", lambda: ExamplePlugin("factory")),
        )
    )
    report = discovery.discover()
    assert report.discovered == 3
    assert tuple(item.manifest.name for item in report.results if item.manifest) == (
        "example",
        "factory",
        "instance",
    )


def test_reports_incompatible_framework_and_missing_capabilities() -> None:
    discovery = PluginDiscovery(
        framework_version="0.8.7",
        entry_points=lambda: (
            FakeEntryPoint("future", ExamplePlugin("future", minimum="1.0.0")),
            FakeEntryPoint("storage", ExamplePlugin("storage", required=frozenset({"storage"}))),
        ),
    )
    report = discovery.discover()
    assert report.incompatible == 2
    assert "requires framework >= 1.0.0" in (report.results[0].message or "")
    assert "missing capabilities storage" in (report.results[1].message or "")


def test_manifest_field_types_are_validated() -> None:
    from src.plugins import manifest_from_mapping

    try:
        manifest_from_mapping({"name": 42, "version": "1.0.0", "description": "Invalid"})
    except TypeError as error:
        assert "fields must be strings: name" in str(error)
    else:
        raise AssertionError("A numeric plugin name must be rejected.")


def test_framework_capability_makes_plugin_compatible() -> None:
    discovery = PluginDiscovery(
        capabilities=frozenset({"storage"}),
        entry_points=lambda: (
            FakeEntryPoint("storage", ExamplePlugin("storage", required=frozenset({"storage"}))),
        ),
    )
    assert discovery.discover().discovered == 1


def test_broken_entry_points_are_isolated() -> None:
    discovery = PluginDiscovery(
        entry_points=lambda: (
            FakeEntryPoint("broken", RuntimeError("boom")),
            FakeEntryPoint("working", ExamplePlugin("working")),
        )
    )
    report = discovery.discover()
    assert report.broken == 1
    assert report.discovered == 1
    assert "RuntimeError: boom" in (report.results[0].message or "")


def test_entry_point_enumeration_failure_is_reported() -> None:
    def fail():
        raise OSError("metadata unavailable")

    report = PluginDiscovery(entry_points=fail).discover()
    assert report.broken == 1
    assert report.results[0].source == "entry-points"


def write_local_plugin(directory: Path, *, manifest_name: str = "local") -> None:
    directory.mkdir()
    (directory / "plugin.py").write_text(
        "from src.plugins import Plugin, PluginManifest\n"
        "class LocalPlugin(Plugin):\n"
        "    @property\n"
        "    def manifest(self):\n"
        f"        return PluginManifest('{manifest_name}', '1.0.0', 'Local plugin')\n",
        encoding="utf-8",
    )
    (directory / "sarathi-plugin.json").write_text(
        json.dumps(
            {
                "name": manifest_name,
                "version": "1.0.0",
                "description": "Local plugin",
                "entry": "plugin.py:LocalPlugin",
            }
        ),
        encoding="utf-8",
    )


def test_discovers_local_development_plugin(tmp_path: Path) -> None:
    plugin_path = tmp_path / "local-plugin"
    write_local_plugin(plugin_path)
    report = PluginDiscovery(local_paths=(plugin_path,), entry_points=lambda: ()).discover()
    assert report.discovered == 1
    assert report.results[0].manifest.name == "local"  # type: ignore[union-attr]
    assert isinstance(report.results[0].plugin, Plugin)


def test_invalid_local_manifest_does_not_block_other_paths(tmp_path: Path) -> None:
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "sarathi-plugin.json").write_text("not json", encoding="utf-8")
    working = tmp_path / "working"
    write_local_plugin(working, manifest_name="working")
    report = PluginDiscovery(
        local_paths=(working, broken),
        entry_points=lambda: (),
    ).discover()
    assert report.broken == 1
    assert report.discovered == 1


def test_duplicate_discovered_names_are_reported() -> None:
    discovery = PluginDiscovery(
        entry_points=lambda: (
            FakeEntryPoint("alpha", ExamplePlugin("same")),
            FakeEntryPoint("beta", ExamplePlugin("same")),
        )
    )
    report = discovery.discover()
    assert report.discovered == 1
    assert report.broken == 1
    assert "Duplicate discovered plugin name" in (report.results[1].message or "")


def test_discovery_cache_and_refresh_are_explicit() -> None:
    calls = 0

    def entries():
        nonlocal calls
        calls += 1
        return (FakeEntryPoint("example", ExamplePlugin()),)

    discovery = PluginDiscovery(entry_points=entries)
    assert discovery.discover().cached is False
    assert discovery.discover().cached is True
    assert calls == 1
    assert discovery.discover(refresh=True).cached is False
    assert calls == 2


def test_report_is_machine_readable_and_human_readable() -> None:
    from src.plugins import render_discovery_report

    report = PluginDiscovery(
        entry_points=lambda: (FakeEntryPoint("example", ExamplePlugin()),)
    ).discover()
    assert report.to_dict()["summary"]["discovered"] == 1
    assert "[DISCOVERED] example" in render_discovery_report(report)
