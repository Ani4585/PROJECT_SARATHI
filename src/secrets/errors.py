"""Secrets management exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class SecretsError(SarathiException):
    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message, error_code="SECRETS_ERROR", details=details)


class MissingSecretError(SecretsError, KeyError):
    def __init__(self, key: str) -> None:
        SecretsError.__init__(
            self,
            f"Required secret is not available: {key}",
            details={"key": key},
        )


class StaleSecretError(SecretsError):
    pass


class SecretSerializationError(SecretsError):
    pass


class SecretProviderError(SecretsError):
    pass
