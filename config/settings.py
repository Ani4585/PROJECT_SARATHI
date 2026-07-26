"""
PROJECT SARATHI

Application settings.
"""

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


class Settings:
    """Central application settings."""

    APP_NAME = APP_NAME
    VERSION = VERSION
    AUTHOR = AUTHOR

    ENVIRONMENT = ENVIRONMENT

    LOG_LEVEL = DEFAULT_LOG_LEVEL

    PROJECT_ROOT = PROJECT_ROOT
    DATA_DIR = DATA_DIR
    LOG_DIR = LOG_DIR


settings = Settings()
class Settings:
    """Central application settings."""

    APP_NAME = APP_NAME
    VERSION = VERSION
    AUTHOR = AUTHOR

    ENVIRONMENT = ENVIRONMENT

    LOG_LEVEL = DEFAULT_LOG_LEVEL

    PROJECT_ROOT = PROJECT_ROOT
    DATA_DIR = DATA_DIR
    LOG_DIR = LOG_DIR


settings = Settings()