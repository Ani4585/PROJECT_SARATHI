"""HTTP and ASGI boundary exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class HttpError(SarathiException):
    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message, error_code="HTTP_ERROR", details=details)


class InvalidScopeError(HttpError):
    pass


class InvalidMessageError(HttpError):
    pass


class RequestBodyTooLargeError(HttpError):
    pass


class ClientDisconnectedError(HttpError):
    pass


class UnsupportedProtocolError(HttpError):
    pass


class ResponseStreamError(HttpError):
    pass


class LifespanProtocolError(HttpError):
    pass


class ServerAdapterUnavailableError(HttpError):
    pass
