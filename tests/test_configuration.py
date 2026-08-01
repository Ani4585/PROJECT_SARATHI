"""Tests for the M13 layered configuration engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.settings import load_settings
from src.configuration import (
    Configuration,
    ConfigurationError,
    ConfigurationField,
    ConfigurationLoader,
    EnvironmentSource,
    InvalidConfigurationError,
    MappingSource,
    MissingConfigurationError,
    UnknownConfigurationError,
)


def test_configuration_normalizes_keys_and_is_immutable() -> None:
    configuration = Configuration({"Database.Host": "localhost"})
    assert configuration["database.host"] == "localhost"
    with pytest.raises(TypeError):
        configuration._values["database.host"] = "changed"  # type: ignore[index]


def test_configuration_require_raises_specific_error() -> None:
    with pytest.raises(MissingConfigurationError):
        Configuration({}).require("missing")


def test_configuration_returns_a_section() -> None:
    configuration = Configuration(
        {"database.host": "localhost", "database.port": 5432, "feature": True}
    )
    assert configuration.section("database") == {"host": "localhost", "port": 5432}


def test_configuration_redacts_secrets() -> None:
    configuration = Configuration(
        {"api.token": "secret"}, secret_keys=frozenset({"api.token"})
    )
    assert configuration.as_dict() == {"api.token": "********"}
    assert configuration.as_dict(redact_secrets=False) == {"api.token": "secret"}


def test_field_rejects_blank_key() -> None:
    with pytest.raises(ValueError):
        ConfigurationField(" ")


def test_field_rejects_required_default_combination() -> None:
    with pytest.raises(ValueError):
        ConfigurationField("port", required=True, default=80)


@pytest.mark.parametrize(
    ("raw", "expected"),
    (("true", True), ("YES", True), ("0", False), (False, False)),
)
def test_boolean_field_conversion(raw: object, expected: bool) -> None:
    field = ConfigurationField("enabled", bool)
    assert field.resolve({"enabled": raw}) is expected


def test_field_reports_conversion_error() -> None:
    with pytest.raises(InvalidConfigurationError):
        ConfigurationField("port", int).resolve({"port": "not-a-number"})


def test_field_reports_validation_failure() -> None:
    field = ConfigurationField("port", int, validator=lambda value: value > 0)
    with pytest.raises(InvalidConfigurationError):
        field.resolve({"port": "0"})


def test_mapping_source_returns_detached_normalized_values() -> None:
    values = {"Service__Port": 8000}
    source = MappingSource("base", values)
    loaded = source.load()
    values["Service__Port"] = 9000
    assert loaded == {"service.port": 8000}


def test_environment_source_filters_prefix_and_normalizes_keys() -> None:
    source = EnvironmentSource(
        environment={"SARATHI_DATABASE__HOST": "db", "UNRELATED": "ignored"}
    )
    assert source.load() == {"database.host": "db"}


def test_loader_applies_later_source_precedence_and_types() -> None:
    loader = ConfigurationLoader(
        (ConfigurationField("port", int),),
        (
            MappingSource("defaults", {"port": 8000}),
            MappingSource("override", {"port": "9000"}),
        ),
    )
    assert loader.source_names == ("defaults", "override")
    assert loader.load()["port"] == 9000


def test_loader_supplies_defaults_and_optional_none() -> None:
    loader = ConfigurationLoader(
        (
            ConfigurationField("host", default="localhost"),
            ConfigurationField("token", secret=True),
        ),
        (MappingSource("empty", {}),),
    )
    assert loader.load().as_dict() == {"host": "localhost", "token": "********"}


def test_loader_rejects_missing_required_value() -> None:
    loader = ConfigurationLoader(
        (ConfigurationField("token", required=True),),
        (MappingSource("empty", {}),),
    )
    with pytest.raises(MissingConfigurationError):
        loader.load()


def test_loader_rejects_unknown_values_by_default() -> None:
    loader = ConfigurationLoader(
        (ConfigurationField("known"),),
        (MappingSource("values", {"known": "yes", "extra": "no"}),),
    )
    with pytest.raises(UnknownConfigurationError):
        loader.load()


def test_loader_can_preserve_unknown_values_explicitly() -> None:
    loader = ConfigurationLoader(
        (ConfigurationField("known"),),
        (MappingSource("values", {"known": "yes", "extra": 3}),),
        allow_unknown=True,
    )
    assert loader.load()["extra"] == 3


def test_loader_wraps_source_failure() -> None:
    class BrokenSource:
        name = "broken"

        def load(self) -> dict[str, object]:
            raise RuntimeError("boom")

    loader = ConfigurationLoader(
        (ConfigurationField("value"),),
        (BrokenSource(),),
    )
    with pytest.raises(ConfigurationError, match="broken"):
        loader.load()


def test_application_settings_keep_defaults() -> None:
    settings = load_settings({})
    assert settings.APP_NAME == "PROJECT SARATHI"
    assert settings.LOG_LEVEL == "INFO"
    assert isinstance(settings.PROJECT_ROOT, Path)


def test_application_settings_accept_environment_overrides() -> None:
    settings = load_settings(
        {"SARATHI_ENVIRONMENT": "test", "SARATHI_LOG_LEVEL": "debug"}
    )
    assert settings.ENVIRONMENT == "test"
    assert settings.LOG_LEVEL == "DEBUG"
