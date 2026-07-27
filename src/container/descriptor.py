"""
PROJECT SARATHI

Service Descriptor

Represents a typed service registration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .lifetimes import ServiceLifetime


@dataclass(slots=True)
class ServiceDescriptor:
    """
    Describes a typed service registration.
    """

    # Public service contract
    service_type: type

    # Concrete implementation
    implementation_type: type

    # Service lifetime
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON

    # Cached singleton instance
    instance: Any | None = None

    constructor_dependencies: list[type] | None = None

    constructor_cached: bool = False

    build_count: int = 0

    # Cached constructor dependency metadata
    constructor_dependencies: list[type] = field(
        default_factory=list
    )