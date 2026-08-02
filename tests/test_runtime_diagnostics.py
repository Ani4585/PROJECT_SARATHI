"""Tests for official M16 safe-share runtime diagnostics."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts.tooling.cli.commands.diagnostics import DiagnosticsCommand
from scripts.tooling.cli.context import CommandContext
from src.configuration import Configuration
from src.container import ServiceContainer
from src.runtime_diagnostics import (
    REDACTED,
    DiagnosticBundleJsonRenderer,
    DiagnosticBundleTextRenderer,
    DiagnosticBundleWriter,
    DiagnosticSectionStatus,
    RuntimeDiagnosticCollector,
    SafeShareRedactor,
)


def test_redactor_masks_sensitive_keys_and_home_paths(tmp_path: Path) -> None:
    redactor = SafeShareRedactor(tmp_path)
    result = redactor.redact(
        {
            "api_key": "secret-value",
            "nested": {"password": "hidden"},
            "path": tmp_path / "project" / "file.txt",
        }
    )
    assert result["api_key"] == REDACTED
    assert result["nested"]["password"] == REDACTED
    assert result["path"] == "<HOME>\\project\\file.txt"


def test_configuration_snapshot_respects_declared_and_heuristic_secrets() -> None:
    configuration = Configuration(
        {"public": "visible", "declared": "secret", "access_token": "token"},
        secret_keys=frozenset({"declared"}),
    )
    bundle = RuntimeDiagnosticCollector().collect(configuration=configuration)
    section = next(item for item in bundle.sections if item.name == "configuration")
    assert section.data["public"] == "visible"
    assert section.data["declared"] == REDACTED
    assert section.data["access_token"] == REDACTED
    assert bundle.safe_to_share is True


def test_collector_inspects_services_lifetimes_and_dependency_edges() -> None:
    class Dependency:
        pass

    class Service:
        pass

    container = ServiceContainer()
    container.register_type(Dependency, Dependency())
    container.register_type(Service, Service())
    container.dependency_graph.add_node(Service)
    container.dependency_graph.add_node(Dependency)
    container.dependency_graph.connect(Service, Dependency)
    bundle = RuntimeDiagnosticCollector().collect(container=container)
    services = next(item for item in bundle.sections if item.name == "services").data
    traces = next(item for item in bundle.sections if item.name == "dependency_traces").data
    assert [item["service"] for item in services["registrations"]] == ["Dependency", "Service"]
    assert services["registrations"][0]["lifetime"] == "singleton"
    assert {item["service"]: item["dependencies"] for item in traces["edges"]}["Service"] == ["Dependency"]


def test_missing_optional_subsystems_are_partial_not_failed() -> None:
    bundle = RuntimeDiagnosticCollector().collect()
    statuses = {section.name: section.status for section in bundle.sections}
    assert statuses["runtime"] is DiagnosticSectionStatus.COMPLETE
    assert statuses["services"] is DiagnosticSectionStatus.PARTIAL
    assert statuses["configuration"] is DiagnosticSectionStatus.PARTIAL
    assert bundle.failures == 0


def test_collector_isolates_partial_failure() -> None:
    class BrokenConfiguration:
        def as_dict(self, **kwargs):
            del kwargs
            raise RuntimeError("unavailable")

    bundle = RuntimeDiagnosticCollector().collect(configuration=BrokenConfiguration())
    configuration = next(item for item in bundle.sections if item.name == "configuration")
    assert configuration.status is DiagnosticSectionStatus.FAILED
    assert configuration.error == "RuntimeError: unavailable"
    assert bundle.failures == 1
    assert len(bundle.sections) == 6


def test_bundle_writer_and_renderers(tmp_path: Path) -> None:
    bundle = RuntimeDiagnosticCollector().collect()
    path = DiagnosticBundleWriter().write_json(bundle, tmp_path / "bundle.json")
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["safe_to_share"] is True
    assert "Safe to share: YES" in DiagnosticBundleTextRenderer().render(bundle)
    assert json.loads(DiagnosticBundleJsonRenderer().render(bundle))["summary"]["sections"] == 6


def test_diagnostics_command_writes_safe_share_bundle(tmp_path: Path, capsys) -> None:
    output = tmp_path / "reports" / "bundle.json"
    exit_code = DiagnosticsCommand().execute(
        CommandContext(tmp_path, "python"),
        Namespace(format="json", output=output),
    )
    rendered = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output.is_file()
    assert rendered["safe_to_share"] is True
