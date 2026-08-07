"""
PROJECT SARATHI

Dependency Injection Container Package.
"""
from .resolver import DependencyResolver
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
    "DependencyResolver",
    "ServiceLifetime",
    "ContainerError",
    "ServiceNotFoundError",
    "ServiceAlreadyRegisteredError",
]
from .bootstrap import bootstrap_container

from .scope import RequestScope, ServiceScope
from .exceptions import ScopeNotFoundError
