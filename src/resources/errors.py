"""Managed-resource framework exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class ResourceError(SarathiException):
    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message, error_code="RESOURCE_ERROR", details=details)


class ResourceRegistrationError(ResourceError):
    pass


class ResourceAcquisitionError(ResourceError):
    pass


class ResourceCleanupError(ResourceError):
    pass


class ResourceLeakError(ResourceCleanupError):
    pass


class ResourceUnavailableError(ResourceError):
    pass
