"""Synchronous, failure-isolated domain event bus."""

from __future__ import annotations

from .event import DomainEvent
from .registry import EventHandlerRegistry, Handler
from .report import EventDelivery, PublicationReport


def _handler_name(handler: Handler) -> str:
    return getattr(handler, "__qualname__", type(handler).__qualname__)


class EventBus:
    """Publish domain events to ordered handlers without fail-fast coupling."""

    def __init__(self, registry: EventHandlerRegistry | None = None) -> None:
        self._registry = registry or EventHandlerRegistry()

    @property
    def registry(self) -> EventHandlerRegistry:
        return self._registry

    def subscribe(self, event_type: type[DomainEvent], handler: Handler) -> None:
        self._registry.subscribe(event_type, handler)

    def unsubscribe(self, event_type: type[DomainEvent], handler: Handler) -> bool:
        return self._registry.unsubscribe(event_type, handler)

    def publish(self, event: DomainEvent) -> PublicationReport:
        if not isinstance(event, DomainEvent):
            raise TypeError("Only DomainEvent instances can be published.")

        deliveries: list[EventDelivery] = []
        for handler in self._registry.handlers_for(event):
            try:
                method = getattr(handler, "handle", None)
                if callable(method):
                    method(event)
                elif callable(handler):
                    handler(event)
                else:
                    raise TypeError("Event handler must be callable or define handle().")
            except Exception as error:
                deliveries.append(
                    EventDelivery(
                        handler_name=_handler_name(handler),
                        succeeded=False,
                        error=f"{type(error).__name__}: {error}",
                    )
                )
            else:
                deliveries.append(
                    EventDelivery(handler_name=_handler_name(handler), succeeded=True)
                )

        return PublicationReport(
            event_id=event.event_id,
            event_type=type(event).__name__,
            deliveries=tuple(deliveries),
        )
