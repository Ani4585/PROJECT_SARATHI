"""
PROJECT SARATHI

Service Descriptor

Represents a typed service registration and its
cached constructor metadata.
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

    service_type: type
    implementation_type: type

    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    instance: Any | None = None

    constructor_dependencies: list[type] = field(
        default_factory=list
    )

    constructor_cached: bool = False
    build_count: int = 0