"""
PROJECT SARATHI

Service Descriptor

Represents a typed service registration.
"""

from __future__ import annotations

from dataclasses import dataclass
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