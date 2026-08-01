"""Application messaging exceptions."""

from __future__ import annotations

from src.exceptions.base import SarathiException


class MessagingError(SarathiException):
    """Base application messaging failure."""


class MessageHandlerNotFoundError(MessagingError):
    """Raised when no handler exists for a message type."""

    def __init__(self, message_type: type[object]) -> None:
        super().__init__(
            f"No handler is registered for {message_type.__name__}.",
            error_code="MESSAGE_HANDLER_NOT_FOUND",
            details={"message_type": message_type.__name__},
        )


class MessageHandlerAlreadyRegisteredError(MessagingError):
    """Raised when a message type receives a second handler."""

    def __init__(self, message_type: type[object]) -> None:
        super().__init__(
            f"A handler is already registered for {message_type.__name__}.",
            error_code="MESSAGE_HANDLER_ALREADY_REGISTERED",
            details={"message_type": message_type.__name__},
        )
