"""Typed command and query handler registry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from .exceptions import (
    MessageHandlerAlreadyRegisteredError,
    MessageHandlerNotFoundError,
)
from .message import Command, Message, Query


class MessageHandler(Protocol):
    """Object-style application message handler."""

    def handle(self, message: Message) -> object:
        """Handle a command or query."""


Handler = MessageHandler | Callable[[Any], object]


class MessageHandlerRegistry:
    """Store exactly one typed handler for each application message type."""

    def __init__(self) -> None:
        self._handlers: dict[type[Message], Handler] = {}

    def register_command(self, command_type: type[Command], handler: Handler) -> None:
        self._register(command_type, Command, handler)

    def register_query(self, query_type: type[Query], handler: Handler) -> None:
        self._register(query_type, Query, handler)

    def _register(
        self,
        message_type: type[Message],
        expected_base: type[Message],
        handler: Handler,
    ) -> None:
        if not isinstance(message_type, type) or not issubclass(message_type, expected_base):
            raise TypeError(f"Message type must inherit from {expected_base.__name__}.")
        if message_type in self._handlers:
            raise MessageHandlerAlreadyRegisteredError(message_type)
        if not callable(handler) and not callable(getattr(handler, "handle", None)):
            raise TypeError("Message handler must be callable or define handle().")
        self._handlers[message_type] = handler

    def get(self, message_type: type[Message]) -> Handler:
        try:
            return self._handlers[message_type]
        except KeyError as error:
            raise MessageHandlerNotFoundError(message_type) from error

    @property
    def registrations(self) -> int:
        return len(self._handlers)
