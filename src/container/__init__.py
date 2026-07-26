"""
PROJECT SARATHI

Dependency Injection Container Package.
"""

from .container import ServiceContainer
from .exceptions import (
    ContainerError,
    ServiceAlreadyRegisteredError,
    ServiceNotFoundError,
)
from .lifetimes import ServiceLifetime
from .provider import FactoryProvider
from .registry import (
    ServiceDefinition,
    ServiceRegistry,
)

__all__ = [
    "ServiceContainer",
    "bootstrap_container",
    "ServiceRegistry",
    "ServiceDefinition",
    "FactoryProvider",
    "ServiceLifetime",
    "ContainerError",
    "ServiceNotFoundError",
    "ServiceAlreadyRegisteredError",
]
from .bootstrap import bootstrap_container
