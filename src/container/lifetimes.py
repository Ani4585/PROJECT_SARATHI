"""PROJECT SARATHI Service lifetime definitions."""

from enum import Enum


class ServiceLifetime(str, Enum):
    """Supported dependency lifetimes."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"
    REQUEST_SCOPED = "request_scoped"
