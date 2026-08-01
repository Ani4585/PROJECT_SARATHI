"""Domain event handler contracts."""

from __future__ import annotations

from typing import Protocol, TypeVar

from .event import DomainEvent


EventT = TypeVar("EventT", bound=DomainEvent, contravariant=True)


class EventHandler(Protocol[EventT]):
    """Handle one type of domain event."""

    def handle(self, event: EventT) -> None:
        """React to a published event."""
