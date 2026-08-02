"""Tests for the official M26 serialization framework."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from src.serialization import (
    JsonSerializer,
    MigrationError,
    MigrationRegistry,
    ObjectCodec,
    SerializationDecodeError,
    SerializationEncodeError,
    SerializationTypeError,
    SerializerNotFoundError,
    SerializerRegistry,
    TomlSerializer,
    TypeCodecRegistry,
    TypedSerializer,
    VersionedSerializer,
    YamlSerializer,
    create_serializer_registry,
)


def test_json_is_deterministic_unicode_and_round_trips_nested_data() -> None:
    serializer = JsonSerializer()
    value = {"z": [1, True, None], "a": "Sārathi"}
    document = serializer.dumps(value)
    assert document == '{"a":"Sārathi","z":[1,true,null]}'
    assert serializer.loads(document) == value


def test_json_wraps_malformed_and_unsupported_values() -> None:
    serializer = JsonSerializer()
    with pytest.raises(SerializationDecodeError, match="JSON decoding failed"):
        serializer.loads('{"broken":')
    with pytest.raises(SerializationEncodeError, match="JSON encoding failed"):
        serializer.dumps(float("nan"))
    with pytest.raises(SerializationEncodeError):
        serializer.dumps(object())


def test_serializer_registry_resolves_names_and_media_types() -> None:
    registry = SerializerRegistry()
    serializer = JsonSerializer()
    registry.register(serializer)
    assert registry.names() == ("json",)
    assert registry.get("JSON") is serializer
    assert registry.for_media_type("application/json; charset=utf-8") is serializer
    assert registry.loads("json", registry.dumps("json", {"value": 1})) == {"value": 1}
    with pytest.raises(ValueError, match="already registered"):
        registry.register(JsonSerializer())
    with pytest.raises(SerializerNotFoundError):
        registry.get("missing")


def test_default_registry_exposes_all_standard_adapters() -> None:
    assert create_serializer_registry().names() == ("json", "toml", "yaml")
    assert create_serializer_registry(include_yaml=False, include_toml=False).names() == ("json",)


def test_yaml_safe_adapter_round_trips_and_reports_malformed_input() -> None:
    serializer = YamlSerializer()
    value = {"service": {"port": 8000}, "enabled": True}
    assert serializer.loads(serializer.dumps(value)) == value
    with pytest.raises(SerializationDecodeError, match="YAML decoding failed"):
        serializer.loads("service: [")


def test_toml_adapter_round_trips_nested_tables_and_lists() -> None:
    serializer = TomlSerializer()
    value = {
        "title": "SARATHI",
        "ports": [8000, 8001],
        "service": {"enabled": True, "ratio": 1.5},
    }
    document = serializer.dumps(value)
    assert "[service]" in document
    assert serializer.loads(document) == value


def test_toml_rejects_invalid_roots_values_and_documents() -> None:
    serializer = TomlSerializer()
    with pytest.raises(SerializationEncodeError, match="root must be a mapping"):
        serializer.dumps([1, 2])
    with pytest.raises(SerializationEncodeError, match="Unsupported TOML value"):
        serializer.dumps({"value": None})
    with pytest.raises(SerializationDecodeError, match="TOML decoding failed"):
        serializer.loads("broken = [")


def test_custom_object_codec_round_trips_nested_values() -> None:
    codecs = TypeCodecRegistry()
    codecs.register(
        ObjectCodec(
            "decimal",
            Decimal,
            lambda value: str(value),
            lambda value: Decimal(str(value)),
        )
    )
    serializer = TypedSerializer(JsonSerializer(), codecs)
    value = {"amounts": [Decimal("10.25"), Decimal("2.50")]}
    restored = serializer.loads(serializer.dumps(value))
    assert restored == value
    assert all(isinstance(item, Decimal) for item in restored["amounts"])


@dataclass(frozen=True, slots=True)
class Address:
    city: str


@dataclass(frozen=True, slots=True)
class User:
    name: str
    address: Address
    roles: tuple[str, ...]


def test_registered_dataclasses_restore_nested_types_and_tuples() -> None:
    codecs = TypeCodecRegistry()
    codecs.register_dataclass(Address)
    codecs.register_dataclass(User, type_name="user")
    serializer = TypedSerializer(JsonSerializer(), codecs)
    value = User("Anirudh", Address("Bengaluru"), ("admin", "author"))
    restored = serializer.loads(serializer.dumps(value))
    assert restored == value
    assert isinstance(restored, User)
    assert isinstance(restored.address, Address)
    assert isinstance(restored.roles, tuple)


def test_reserved_mapping_keys_are_escaped_without_data_loss() -> None:
    serializer = TypedSerializer(JsonSerializer(), TypeCodecRegistry())
    value = {"$sarathi.type": "ordinary", "$sarathi.value": {"nested": True}}
    assert serializer.loads(serializer.dumps(value)) == value


def test_typed_serializer_rejects_unregistered_and_malformed_types() -> None:
    serializer = TypedSerializer(JsonSerializer(), TypeCodecRegistry())
    with pytest.raises(SerializationTypeError, match="No object codec"):
        serializer.dumps(object())
    with pytest.raises(SerializationTypeError, match="mapping keys must be strings"):
        serializer.dumps({1: "value"})
    with pytest.raises(SerializationTypeError, match="not registered"):
        serializer.loads('{"$sarathi.type":"unknown","$sarathi.value":{}}')
    with pytest.raises(SerializationDecodeError, match="unexpected fields"):
        serializer.loads(
            '{"$sarathi.type":"builtins.tuple","$sarathi.value":[],"extra":true}'
        )


def test_current_versioned_document_round_trips() -> None:
    serializer = VersionedSerializer(
        JsonSerializer(),
        schema="project.settings",
        version=2,
    )
    value = {"name": "SARATHI"}
    document = serializer.dumps(value)
    assert '"$version":2' in document
    assert serializer.loads(document) == value


def test_migration_registry_applies_ordered_forward_chain() -> None:
    migrations = MigrationRegistry()
    migrations.register(
        "person",
        1,
        2,
        lambda value: {"name": value["full_name"]},
    )
    migrations.register(
        "person",
        2,
        3,
        lambda value: {**value, "active": True},
    )
    serializer = VersionedSerializer(
        JsonSerializer(),
        schema="person",
        version=3,
        migrations=migrations,
    )
    old_document = (
        '{"$schema":"person","$version":1,'
        '"payload":{"full_name":"Anirudh"}}'
    )
    assert serializer.loads(old_document) == {"name": "Anirudh", "active": True}


def test_versioned_serializer_reports_missing_failed_and_future_migrations() -> None:
    serializer = VersionedSerializer(JsonSerializer(), schema="item", version=2)
    with pytest.raises(MigrationError, match="No migration path"):
        serializer.loads('{"$schema":"item","$version":1,"payload":{}}')
    with pytest.raises(MigrationError, match="newer than supported"):
        serializer.loads('{"$schema":"item","$version":3,"payload":{}}')

    migrations = MigrationRegistry()
    migrations.register(
        "item",
        1,
        2,
        lambda value: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    failing = VersionedSerializer(
        JsonSerializer(), schema="item", version=2, migrations=migrations
    )
    with pytest.raises(MigrationError, match="failed: boom"):
        failing.loads('{"$schema":"item","$version":1,"payload":{}}')


def test_versioned_serializer_rejects_wrong_schema_and_invalid_envelope() -> None:
    serializer = VersionedSerializer(JsonSerializer(), schema="expected", version=1)
    with pytest.raises(SerializationDecodeError, match="Unexpected schema"):
        serializer.loads('{"$schema":"other","$version":1,"payload":{}}')
    with pytest.raises(SerializationDecodeError, match="envelope is invalid"):
        serializer.loads('{"$schema":"expected","$version":1}')
    with pytest.raises(ValueError, match="positive integer"):
        VersionedSerializer(JsonSerializer(), schema="expected", version=True)
    with pytest.raises(TypeError, match="must be integers"):
        MigrationRegistry().register("expected", True, 2, lambda value: value)
