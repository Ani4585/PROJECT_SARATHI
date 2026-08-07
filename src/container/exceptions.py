"""
PROJECT SARATHI

Dependency Injection Exceptions.
"""

from src.exceptions import SarathiException


class ContainerError(SarathiException):
    """
    Base exception for dependency injection container errors.
    """

    def __init__(self, message: str, details=None):
        super().__init__(
            message=message,
            error_code="CONTAINER_ERROR",
            details=details,
        )


class ServiceNotFoundError(ContainerError):
    """
    Raised when a requested service is not registered.
    """

    def __init__(self, service_name: str):
        super().__init__(
            message=f"Service '{service_name}' is not registered.",
            details={"service": service_name},
        )


class ServiceAlreadyRegisteredError(ContainerError):
    """
    Raised when attempting to register a duplicate service.
    """

    def __init__(self, service_name: str):
        super().__init__(
            message=f"Service '{service_name}' is already registered.",
            details={"service": service_name},
        )

class ScopeNotFoundError(Exception):
    """Raised when resolving a scoped service outside an active RequestScope."""
    pass
