"""Tests for the M14 domain event system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from src.domain.events import DomainEvent, EventBus, EventHandlerRegistry


@dataclass(frozen=True, slots=True, kw_only=True)
class ItemCreated(DomainEvent):
    item_id: str


def test_domain_event_has_unique_identity_and_aware_timestamp() -> None:
    first = ItemCreated(item_id="one")
    second = ItemCreated(item_id="two")
    assert first.event_id != second.event_id
    assert first.occurred_at.tzinfo is not None


def test_domain_event_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        ItemCreated(item_id="one", occurred_at=datetime.now())


def test_registry_rejects_non_event_type() -> None:
    registry = EventHandlerRegistry()
    with pytest.raises(TypeError):
        registry.subscribe(str, lambda event: None)  # type: ignore[arg-type]


def test_registry_rejects_duplicate_handler_identity() -> None:
    registry = EventHandlerRegistry()
    handler = lambda event: None
    registry.subscribe(ItemCreated, handler)
    with pytest.raises(ValueError):
        registry.subscribe(ItemCreated, handler)


def test_registry_unsubscribes_handler() -> None:
    registry = EventHandlerRegistry()
    handler = lambda event: None
    registry.subscribe(ItemCreated, handler)
    assert registry.subscriptions == 1
    assert registry.unsubscribe(ItemCreated, handler) is True
    assert registry.unsubscribe(ItemCreated, handler) is False
    assert registry.subscriptions == 0


def test_bus_delivers_functions_in_subscription_order() -> None:
    calls: list[str] = []
    bus = EventBus()
    bus.subscribe(ItemCreated, lambda event: calls.append(f"first:{event.item_id}"))
    bus.subscribe(ItemCreated, lambda event: calls.append(f"second:{event.item_id}"))
    report = bus.publish(ItemCreated(item_id="42"))
    assert calls == ["first:42", "second:42"]
    assert report.delivered_handlers == 2
    assert report.succeeded is True


def test_bus_supports_handler_objects() -> None:
    received: list[str] = []

    class Handler:
        def handle(self, event: ItemCreated) -> None:
            received.append(event.item_id)

    bus = EventBus()
    bus.subscribe(ItemCreated, Handler())
    assert bus.publish(ItemCreated(item_id="42")).succeeded is True
    assert received == ["42"]


def test_bus_delivers_base_event_subscriptions() -> None:
    received: list[str] = []
    bus = EventBus()
    bus.subscribe(DomainEvent, lambda event: received.append(type(event).__name__))
    bus.publish(ItemCreated(item_id="42"))
    assert received == ["ItemCreated"]


def test_bus_isolates_handler_failures_and_continues() -> None:
    calls: list[str] = []

    def broken(event: ItemCreated) -> None:
        del event
        raise RuntimeError("boom")

    bus = EventBus()
    bus.subscribe(ItemCreated, broken)
    bus.subscribe(ItemCreated, lambda event: calls.append(event.item_id))
    report = bus.publish(ItemCreated(item_id="42"))
    assert calls == ["42"]
    assert report.failed_handlers == 1
    assert report.succeeded is False
    assert report.deliveries[0].error == "RuntimeError: boom"


def test_bus_reports_zero_delivery_as_success() -> None:
    report = EventBus().publish(ItemCreated(item_id="42"))
    assert report.delivered_handlers == 0
    assert report.succeeded is True


def test_bus_rejects_non_event_instances() -> None:
    with pytest.raises(TypeError):
        EventBus().publish("not-an-event")  # type: ignore[arg-type]
