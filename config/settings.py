"""Backward-compatible application settings backed by layered configuration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from config.constants import (
    APP_NAME,
    VERSION,
    AUTHOR,
    DEFAULT_LOG_LEVEL,
    ENVIRONMENT,
)

from config.paths import (
    PROJECT_ROOT,
    DATA_DIR,
    LOG_DIR,
)
from src.configuration import (
    ConfigurationField,
    ConfigurationLoader,
    EnvironmentSource,
    MappingSource,
)


@dataclass(frozen=True, slots=True)
class Settings:
    """Central application settings with the established attribute names."""

    APP_NAME: str = APP_NAME
    VERSION: str = VERSION
    AUTHOR: str = AUTHOR
    ENVIRONMENT: str = ENVIRONMENT
    LOG_LEVEL: str = DEFAULT_LOG_LEVEL
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = DATA_DIR
    LOG_DIR: Path = LOG_DIR


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    """Load application settings with environment variables taking precedence."""

    defaults = {
        "app_name": APP_NAME,
        "version": VERSION,
        "author": AUTHOR,
        "environment": ENVIRONMENT,
        "log_level": DEFAULT_LOG_LEVEL,
        "project_root": PROJECT_ROOT,
        "data_dir": DATA_DIR,
        "log_dir": LOG_DIR,
    }
    fields = (
        ConfigurationField("app_name"),
        ConfigurationField("version"),
        ConfigurationField("author"),
        ConfigurationField("environment"),
        ConfigurationField(
            "log_level",
            validator=lambda value: value.upper()
            in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
        ),
        ConfigurationField("project_root", Path),
        ConfigurationField("data_dir", Path),
        ConfigurationField("log_dir", Path),
    )
    configuration = ConfigurationLoader(
        fields,
        (
            MappingSource("defaults", defaults),
            EnvironmentSource(environment=environment),
        ),
    ).load()
    return Settings(
        APP_NAME=str(configuration["app_name"]),
        VERSION=str(configuration["version"]),
        AUTHOR=str(configuration["author"]),
        ENVIRONMENT=str(configuration["environment"]),
        LOG_LEVEL=str(configuration["log_level"]).upper(),
        PROJECT_ROOT=Path(configuration["project_root"]),
        DATA_DIR=Path(configuration["data_dir"]),
        LOG_DIR=Path(configuration["log_dir"]),
    )


settings = load_settings()
