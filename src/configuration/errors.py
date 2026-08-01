"""Configuration-specific exceptions for PROJECT SARATHI."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class ConfigurationError(SarathiException):
    """Base error raised by the configuration engine."""

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration value is unavailable."""

    def __init__(self, key: str) -> None:
        super().__init__(
            f"Required configuration value {key!r} is missing.",
            details={"key": key},
        )
        self.error_code = "CONFIGURATION_MISSING"


class InvalidConfigurationError(ConfigurationError):
    """Raised when a configuration value cannot be validated or converted."""

    def __init__(self, key: str, value: object, reason: str) -> None:
        super().__init__(
            f"Configuration value {key!r} is invalid: {reason}",
            details={"key": key, "value": value, "reason": reason},
        )
        self.error_code = "CONFIGURATION_INVALID"


class UnknownConfigurationError(ConfigurationError):
    """Raised when strict loading encounters undeclared keys."""

    def __init__(self, keys: tuple[str, ...]) -> None:
        super().__init__(
            "Unknown configuration keys: " + ", ".join(keys),
            details={"keys": keys},
        )
        self.error_code = "CONFIGURATION_UNKNOWN"
