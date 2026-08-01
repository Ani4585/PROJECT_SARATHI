"""Application message dispatcher with ordered middleware."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol

from .message import Command, Message, Query
from .registry import Handler, MessageHandlerRegistry


NextHandler = Callable[[Message], object]


class MessageMiddleware(Protocol):
    """Wrap application message handling with cross-cutting behavior."""

    def __call__(self, message: Message, next_handler: NextHandler) -> object:
        """Process a message and invoke the remaining pipeline."""


class MessageBus:
    """Dispatch typed commands and queries through ordered middleware."""

    def __init__(
        self,
        registry: MessageHandlerRegistry | None = None,
        middleware: Iterable[MessageMiddleware] = (),
    ) -> None:
        self._registry = registry or MessageHandlerRegistry()
        self._middleware = tuple(middleware)

    @property
    def registry(self) -> MessageHandlerRegistry:
        return self._registry

    @property
    def middleware(self) -> tuple[MessageMiddleware, ...]:
        return self._middleware

    def register_command(self, command_type: type[Command], handler: Handler) -> None:
        self._registry.register_command(command_type, handler)

    def register_query(self, query_type: type[Query], handler: Handler) -> None:
        self._registry.register_query(query_type, handler)

    def send(self, message: Message) -> object:
        if not isinstance(message, (Command, Query)):
            raise TypeError("MessageBus accepts only Command or Query instances.")

        handler = self._registry.get(type(message))

        def invoke_handler(current: Message) -> object:
            method = getattr(handler, "handle", None)
            return method(current) if callable(method) else handler(current)  # type: ignore[operator]

        pipeline: NextHandler = invoke_handler
        for current_middleware in reversed(self._middleware):
            next_handler = pipeline

            def invoke(
                current: Message,
                *,
                middleware: MessageMiddleware = current_middleware,
                following: NextHandler = next_handler,
            ) -> object:
                return middleware(current, following)

            pipeline = invoke

        return pipeline(message)
