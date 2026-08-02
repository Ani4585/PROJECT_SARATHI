"""Caching framework exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class CacheError(SarathiException):
    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message, error_code="CACHE_ERROR", details=details)


class CacheKeyError(CacheError):
    pass


class CacheLoadError(CacheError):
    pass
