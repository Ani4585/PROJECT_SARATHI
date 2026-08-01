"""Ordered domain event handler registry."""

from __future__ import annotations

from collections.abc import Callable

from .event import DomainEvent
from .handler import EventHandler


Handler = EventHandler[DomainEvent] | Callable[[DomainEvent], None]


class EventHandlerRegistry:
    """Register handlers by event type while preserving subscription order."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Handler]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: Handler) -> None:
        if not isinstance(event_type, type) or not issubclass(event_type, DomainEvent):
            raise TypeError("event_type must inherit from DomainEvent.")
        handlers = self._handlers.setdefault(event_type, [])
        if any(registered is handler for registered in handlers):
            raise ValueError("The handler is already subscribed to this event type.")
        handlers.append(handler)

    def unsubscribe(self, event_type: type[DomainEvent], handler: Handler) -> bool:
        handlers = self._handlers.get(event_type, [])
        for index, registered in enumerate(handlers):
            if registered is handler:
                handlers.pop(index)
                if not handlers:
                    self._handlers.pop(event_type, None)
                return True
        return False

    def handlers_for(self, event: DomainEvent) -> tuple[Handler, ...]:
        """Return matching handlers in deterministic registration order."""

        handlers: list[Handler] = []
        for event_type, registered in self._handlers.items():
            if isinstance(event, event_type):
                handlers.extend(registered)
        return tuple(handlers)

    @property
    def subscriptions(self) -> int:
        return sum(len(handlers) for handlers in self._handlers.values())
