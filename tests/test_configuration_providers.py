"""Tests for official M25 configuration providers and reload behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.configuration import (
    ConfigurationChangeKind,
    ConfigurationField,
    ConfigurationLoader,
    ConfigurationManager,
    EnvironmentSource,
    FileSource,
    MappingSource,
)


def test_explicit_priority_wins_independent_of_declaration_order() -> None:
    loader = ConfigurationLoader(
        (ConfigurationField("port", int),),
        (
            MappingSource("high", {"port": "9000"}, priority=100),
            MappingSource("low", {"port": "8000"}, priority=10),
        ),
    )
    configuration = loader.load()
    assert loader.source_names == ("low", "high")
    assert configuration["port"] == 9000
    assert configuration.source_of("port") == "high"
    assert configuration.provenance("port").priority == 100


def test_equal_priority_preserves_later_source_precedence() -> None:
    loader = ConfigurationLoader(
        (ConfigurationField("mode"),),
        (
            MappingSource("first", {"mode": "one"}, priority=10),
            MappingSource("second", {"mode": "two"}, priority=10),
        ),
    )
    assert loader.load()["mode"] == "two"


def test_environment_default_priority_overrides_mapping() -> None:
    loader = ConfigurationLoader(
        (ConfigurationField("service.port", int),),
        (
            EnvironmentSource(environment={"SARATHI_SERVICE__PORT": "9100"}),
            MappingSource("defaults", {"service.port": 8000}),
        ),
    )
    configuration = loader.load()
    assert configuration["service.port"] == 9100
    assert configuration.source_of("service.port") == "environment"


def test_mapping_file_environment_layers_use_declared_precedence(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"host": "file-host", "port": 8500}),
        encoding="utf-8",
    )
    configuration = ConfigurationLoader(
        (ConfigurationField("host"), ConfigurationField("port", int)),
        (
            EnvironmentSource(environment={"SARATHI_PORT": "9000"}),
            FileSource(path),
            MappingSource("defaults", {"host": "default-host", "port": 8000}),
        ),
    ).load()
    assert configuration["host"] == "file-host"
    assert configuration.source_of("host") == "file:settings.json"
    assert configuration["port"] == 9000
    assert configuration.source_of("port") == "environment"


def test_schema_defaults_have_explicit_provenance() -> None:
    configuration = ConfigurationLoader(
        (ConfigurationField("host", default="localhost"),),
        (MappingSource("empty", {}),),
    ).load()
    assert configuration.source_of("host") == "schema-default"
    assert configuration.provenance("host").priority == -1


def test_json_file_provider_flattens_nested_values(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"database": {"host": "db", "port": 5432}, "debug": True}),
        encoding="utf-8",
    )
    source = FileSource(path)
    assert source.load() == {
        "database.host": "db",
        "database.port": 5432,
        "debug": True,
    }


def test_toml_file_provider_loads_tables(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text('[database]\nhost = "db"\nport = 5432\n', encoding="utf-8")
    assert FileSource(path).load() == {
        "database.host": "db",
        "database.port": 5432,
    }


def test_optional_file_provider_tolerates_missing_file(tmp_path: Path) -> None:
    assert FileSource(tmp_path / "missing.json", optional=True).load() == {}
    with pytest.raises(FileNotFoundError):
        FileSource(tmp_path / "missing.json").load()


def test_provider_names_must_be_unique_for_unambiguous_provenance() -> None:
    with pytest.raises(ValueError, match="names must be unique"):
        ConfigurationLoader(
            (ConfigurationField("value"),),
            (
                MappingSource("duplicate", {"value": "one"}),
                MappingSource("duplicate", {"value": "two"}),
            ),
        )


def test_reload_tracks_value_and_provenance_changes() -> None:
    values: dict[str, object] = {"mode": "development", "port": 8000}
    manager = ConfigurationManager(
        ConfigurationLoader(
            (ConfigurationField("mode"), ConfigurationField("port", int)),
            (MappingSource("runtime", values),),
        )
    )
    manager.load()
    values["mode"] = "production"
    report = manager.reload()
    assert report.changed is True
    assert report.configuration["mode"] == "production"
    assert len(report.change_set.changes) == 1
    change = report.change_set.changes[0]
    assert change.key == "mode"
    assert change.kind is ConfigurationChangeKind.UPDATED
    assert change.previous_value == "development"
    assert change.current_value == "production"
    assert change.current_provenance.source == "runtime"  # type: ignore[union-attr]


def test_reload_rereads_changed_file(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"mode": "development"}), encoding="utf-8")
    manager = ConfigurationManager(
        ConfigurationLoader(
            (ConfigurationField("mode"),),
            (FileSource(path),),
        )
    )
    manager.load()
    path.write_text(json.dumps({"mode": "production"}), encoding="utf-8")
    report = manager.reload()
    assert report.configuration["mode"] == "production"
    assert report.change_set.changes[0].previous_value == "development"


def test_same_value_from_new_provider_is_a_provenance_change() -> None:
    low_values: dict[str, object] = {"mode": "same"}
    high_values: dict[str, object] = {}
    manager = ConfigurationManager(
        ConfigurationLoader(
            (ConfigurationField("mode"),),
            (
                MappingSource("low", low_values, priority=10),
                MappingSource("high", high_values, priority=20),
            ),
        )
    )
    manager.load()
    high_values["mode"] = "same"
    report = manager.reload()
    change = report.change_set.changes[0]
    assert change.kind is ConfigurationChangeKind.UPDATED
    assert change.previous_value == change.current_value == "same"
    assert change.previous_provenance.source == "low"  # type: ignore[union-attr]
    assert change.current_provenance.source == "high"  # type: ignore[union-attr]


def test_reload_notifies_in_order_and_unsubscribe_is_idempotent() -> None:
    values: dict[str, object] = {"value": "one"}
    manager = ConfigurationManager(
        ConfigurationLoader(
            (ConfigurationField("value"),),
            (MappingSource("runtime", values),),
        )
    )
    manager.load()
    calls: list[str] = []
    manager.subscribe(lambda changes: calls.append("first"))
    unsubscribe = manager.subscribe(lambda changes: calls.append("second"))
    values["value"] = "two"
    assert manager.reload().passed is True
    assert calls == ["first", "second"]
    unsubscribe()
    unsubscribe()
    values["value"] = "three"
    manager.reload()
    assert calls == ["first", "second", "first"]


def test_listener_failure_is_isolated_and_new_configuration_remains_active() -> None:
    values: dict[str, object] = {"value": "one"}
    manager = ConfigurationManager(
        ConfigurationLoader(
            (ConfigurationField("value"),),
            (MappingSource("runtime", values),),
        )
    )
    manager.load()
    observed: list[str] = []

    def broken(changes) -> None:
        raise RuntimeError("listener failed")

    manager.subscribe(broken)
    manager.subscribe(lambda changes: observed.append(str(changes.current["value"])))
    values["value"] = "two"
    report = manager.reload()
    assert report.passed is False
    assert "RuntimeError: listener failed" in report.notification_failures[0].message
    assert observed == ["two"]
    assert manager.current["value"] == "two"


def test_no_change_does_not_notify_listeners() -> None:
    manager = ConfigurationManager(
        ConfigurationLoader(
            (ConfigurationField("value"),),
            (MappingSource("runtime", {"value": "same"}),),
        )
    )
    manager.load()
    calls: list[str] = []
    manager.subscribe(lambda changes: calls.append("called"))
    report = manager.reload()
    assert report.changed is False
    assert calls == []
