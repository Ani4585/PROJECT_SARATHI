"""Structured domain event publication reports."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EventDelivery:
    """Describe delivery of an event to one handler."""

    handler_name: str
    succeeded: bool
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PublicationReport:
    """Contain all ordered handler-delivery outcomes for one event."""

    event_id: UUID
    event_type: str
    deliveries: tuple[EventDelivery, ...]

    @property
    def delivered_handlers(self) -> int:
        return len(self.deliveries)

    @property
    def failed_handlers(self) -> int:
        return sum(not delivery.succeeded for delivery in self.deliveries)

    @property
    def succeeded(self) -> bool:
        return self.failed_handlers == 0
