"""Public PROJECT SARATHI managed-resource API."""

from .errors import (
    ResourceAcquisitionError,
    ResourceCleanupError,
    ResourceError,
    ResourceLeakError,
    ResourceRegistrationError,
    ResourceUnavailableError,
)
from .health import ResourceRegistryHealthCheck
from .lazy import LazyResource
from .lifecycle import ResourceLifecycle
from .model import (
    ResourceCleanupFailure,
    ResourceCloseReport,
    ResourceDefinition,
    ResourceRegistrySnapshot,
    ResourceRegistryState,
    ResourceState,
)
from .pool import ResourceLease, ResourcePool, ResourcePoolSnapshot
from .registry import ResourceRegistry

__all__ = [
    "LazyResource",
    "ResourceAcquisitionError",
    "ResourceCleanupError",
    "ResourceCleanupFailure",
    "ResourceCloseReport",
    "ResourceDefinition",
    "ResourceError",
    "ResourceLeakError",
    "ResourceLease",
    "ResourceLifecycle",
    "ResourcePool",
    "ResourcePoolSnapshot",
    "ResourceRegistrationError",
    "ResourceRegistry",
    "ResourceRegistryHealthCheck",
    "ResourceRegistrySnapshot",
    "ResourceRegistryState",
    "ResourceState",
    "ResourceUnavailableError",
]
