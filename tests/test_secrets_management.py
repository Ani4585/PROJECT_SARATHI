"""Tests for the official M27 secrets management system."""

from __future__ import annotations

import copy
import json

import pytest

from src.runtime_diagnostics import REDACTED, RuntimeDiagnosticCollector, SafeShareRedactor
from src.secrets import (
    EnvironmentSecretProvider,
    FileSecretProvider,
    MappingSecretProvider,
    MissingSecretError,
    SecretChangeKind,
    SecretManager,
    SecretProviderError,
    SecretSerializationError,
    SecretValue,
    StaleSecretError,
)
from src.serialization import (
    JsonSerializer,
    SerializationEncodeError,
    SerializationTypeError,
    TomlSerializer,
    TypeCodecRegistry,
    TypedSerializer,
    YamlSerializer,
)


class MutableProvider:
    name = "mutable"
    priority = 10

    def __init__(self, values: dict[str, str]) -> None:
        self.values = values
        self.error: Exception | None = None

    def load(self) -> dict[str, str]:
        if self.error is not None:
            raise self.error
        return dict(self.values)


def test_secret_value_masks_all_display_paths_and_requires_explicit_reveal() -> None:
    secret = SecretValue("top-secret")
    assert str(secret) == "********"
    assert repr(secret) == "SecretValue('********')"
    assert f"value={secret}" == "value=********"
    assert secret.reveal() == "top-secret"
    assert "top-secret" not in str([secret])


def test_secret_value_cannot_be_copied_or_pickled_implicitly() -> None:
    secret = SecretValue("never-copy")
    with pytest.raises(SecretSerializationError, match="cannot be serialized"):
        copy.copy(secret)


def test_layered_manager_resolves_precedence_and_provenance() -> None:
    manager = SecretManager(
        [
            MappingSecretProvider("defaults", {"database.password": "old"}, 0),
            MappingSecretProvider("override", {"DATABASE__PASSWORD": "new"}, 50),
        ]
    )
    snapshot = manager.load()
    assert snapshot["DATABASE.PASSWORD"].reveal() == "new"
    assert snapshot.provenance("database.password").provider == "override"
    assert snapshot.safe_summary() == {
        "count": 1,
        "keys": ("database.password",),
        "providers": ("override",),
    }


def test_environment_provider_filters_prefix_and_normalizes_keys() -> None:
    provider = EnvironmentSecretProvider(
        environment={
            "SARATHI_SECRET_API__TOKEN": "token-value",
            "UNRELATED": "ignored",
        }
    )
    assert provider.load() == {"api.token": "token-value"}


def test_json_secret_file_flattens_nested_values(tmp_path) -> None:
    path = tmp_path / "secrets.json"
    path.write_text(json.dumps({"database": {"password": "value"}}), encoding="utf-8")
    provider = FileSecretProvider(path)
    assert provider.load() == {"database.password": "value"}


def test_toml_secret_file_and_optional_missing_file(tmp_path) -> None:
    path = tmp_path / "secrets.toml"
    path.write_text('[service]\ntoken = "value"\n', encoding="utf-8")
    assert FileSecretProvider(path).load() == {"service.token": "value"}
    assert FileSecretProvider(tmp_path / "missing.json", optional=True).load() == {}


def test_secret_file_rejects_non_string_values_and_unsupported_formats(tmp_path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"token": 123}', encoding="utf-8")
    with pytest.raises(SecretProviderError, match="must be a string"):
        FileSecretProvider(invalid).load()
    unsupported = tmp_path / "secrets.txt"
    unsupported.write_text("token=value", encoding="utf-8")
    with pytest.raises(SecretProviderError, match="json or .toml"):
        FileSecretProvider(unsupported).load()


def test_manager_rejects_duplicate_providers_and_missing_secrets() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        SecretManager(
            [
                MappingSecretProvider("same", {}),
                MappingSecretProvider("same", {}),
            ]
        )
    snapshot = SecretManager([MappingSecretProvider("empty", {})]).load()
    with pytest.raises(MissingSecretError, match="not available"):
        snapshot.require("missing")


def test_rotation_invalidates_old_handle_and_emits_metadata_only() -> None:
    provider = MutableProvider({"api.token": "first-value"})
    manager = SecretManager([provider])
    old = manager.load()["api.token"]
    observed = []
    manager.subscribe(observed.append)
    provider.values["api.token"] = "second-value"
    report = manager.reload()
    assert report.changed is True
    assert report.change_set.changes[0].kind is SecretChangeKind.ROTATED
    assert manager.current["api.token"].reveal() == "second-value"
    with pytest.raises(StaleSecretError):
        old.reveal()
    assert "first-value" not in repr(report)
    assert "second-value" not in repr(report)
    assert observed == [report.change_set]


def test_removed_secret_invalidates_stale_handle() -> None:
    provider = MutableProvider({"token": "value"})
    manager = SecretManager([provider])
    old = manager.load()["token"]
    provider.values.clear()
    report = manager.reload()
    assert report.change_set.changes[0].kind is SecretChangeKind.REMOVED
    assert "token" not in manager.current
    with pytest.raises(StaleSecretError):
        old.reveal()


def test_unchanged_reload_preserves_live_handle_and_has_no_notification() -> None:
    provider = MutableProvider({"token": "value"})
    manager = SecretManager([provider])
    original = manager.load()["token"]
    observed = []
    manager.subscribe(observed.append)
    report = manager.reload()
    assert report.changed is False
    assert manager.current["token"] is original
    assert original.reveal() == "value"
    assert observed == []


def test_listener_failures_are_isolated_and_unsubscribe_is_idempotent() -> None:
    provider = MutableProvider({"token": "one"})
    manager = SecretManager([provider])
    manager.load()

    def broken(change_set) -> None:
        del change_set
        raise RuntimeError("listener failed")

    unsubscribe = manager.subscribe(broken)
    provider.values["token"] = "two"
    report = manager.reload()
    assert report.passed is False
    assert report.notification_failures[0].message == "RuntimeError: listener failed"
    unsubscribe()
    unsubscribe()
    provider.values["token"] = "three"
    assert manager.reload().passed is True


def test_failed_reload_is_atomic_and_keeps_existing_secret_live() -> None:
    provider = MutableProvider({"token": "stable"})
    manager = SecretManager([provider])
    original = manager.load()["token"]
    provider.error = RuntimeError("provider unavailable")
    with pytest.raises(SecretProviderError, match="failed to load"):
        manager.reload()
    assert manager.current["token"] is original
    assert original.reveal() == "stable"


def test_serializers_never_emit_secret_plaintext() -> None:
    secret = SecretValue("leak-check-value")
    serializers = (JsonSerializer(), YamlSerializer(), TomlSerializer())
    for serializer in serializers:
        with pytest.raises(SerializationEncodeError) as captured:
            serializer.dumps({"token": secret})
        assert "leak-check-value" not in str(captured.value)
    typed = TypedSerializer(JsonSerializer(), TypeCodecRegistry())
    with pytest.raises(SerializationTypeError, match="cannot be serialized"):
        typed.dumps({"token": secret})


def test_diagnostics_redact_secret_objects_and_report_safe_manager_summary() -> None:
    secret = SecretValue("diagnostic-leak-value")
    assert SafeShareRedactor().redact(secret) == REDACTED
    manager = SecretManager([MappingSecretProvider("memory", {"api.token": "value"})])
    manager.load()
    bundle = RuntimeDiagnosticCollector().collect(secrets=manager)
    section = next(item for item in bundle.sections if item.name == "secrets")
    assert section.data == {
        "count": 1,
        "keys": ["api.token"],
        "providers": ["memory"],
    }
    assert "value" not in str(bundle.to_dict())


def test_secret_snapshots_are_rejected_by_typed_serialization() -> None:
    snapshot = SecretManager([MappingSecretProvider("memory", {"token": "value"})]).load()
    serializer = TypedSerializer(JsonSerializer(), TypeCodecRegistry())
    with pytest.raises(SerializationTypeError, match="cannot be serialized"):
        serializer.dumps(snapshot)
