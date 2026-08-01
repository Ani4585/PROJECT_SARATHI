"""Tests for the M15 application messaging pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.application.messaging import (
    Command,
    MessageBus,
    MessageHandlerAlreadyRegisteredError,
    MessageHandlerNotFoundError,
    MessageHandlerRegistry,
    Query,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateItem(Command):
    name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class FindItem(Query):
    item_id: str


def test_messages_have_unique_identity_and_aware_time() -> None:
    first = CreateItem(name="one")
    second = CreateItem(name="two")
    assert first.message_id != second.message_id
    assert first.created_at.tzinfo is not None


def test_registry_rejects_wrong_message_category() -> None:
    registry = MessageHandlerRegistry()
    with pytest.raises(TypeError):
        registry.register_command(FindItem, lambda query: None)  # type: ignore[arg-type]


def test_registry_rejects_duplicate_handler() -> None:
    registry = MessageHandlerRegistry()
    registry.register_command(CreateItem, lambda command: None)
    with pytest.raises(MessageHandlerAlreadyRegisteredError):
        registry.register_command(CreateItem, lambda command: None)


def test_registry_rejects_invalid_handler() -> None:
    with pytest.raises(TypeError):
        MessageHandlerRegistry().register_query(FindItem, object())  # type: ignore[arg-type]


def test_bus_dispatches_command_function() -> None:
    received: list[str] = []
    bus = MessageBus()
    bus.register_command(CreateItem, lambda command: received.append(command.name))
    result = bus.send(CreateItem(name="compost"))
    assert received == ["compost"]
    assert result is None


def test_bus_dispatches_query_and_returns_result() -> None:
    bus = MessageBus()
    bus.register_query(FindItem, lambda query: {"id": query.item_id})
    assert bus.send(FindItem(item_id="42")) == {"id": "42"}


def test_bus_supports_object_handler() -> None:
    class Handler:
        def handle(self, query: FindItem) -> str:
            return query.item_id

    bus = MessageBus()
    bus.register_query(FindItem, Handler())
    assert bus.send(FindItem(item_id="42")) == "42"


def test_bus_raises_specific_error_for_missing_handler() -> None:
    with pytest.raises(MessageHandlerNotFoundError):
        MessageBus().send(FindItem(item_id="42"))


def test_middleware_wraps_handler_in_declared_order() -> None:
    calls: list[str] = []

    def first(message, next_handler):
        calls.append("first-before")
        result = next_handler(message)
        calls.append("first-after")
        return result

    def second(message, next_handler):
        calls.append("second-before")
        result = next_handler(message)
        calls.append("second-after")
        return result

    bus = MessageBus(middleware=(first, second))
    bus.register_query(FindItem, lambda query: calls.append("handler") or query.item_id)
    assert bus.send(FindItem(item_id="42")) == "42"
    assert calls == [
        "first-before",
        "second-before",
        "handler",
        "second-after",
        "first-after",
    ]


def test_middleware_can_short_circuit_handler() -> None:
    bus = MessageBus(middleware=(lambda message, next_handler: "cached",))
    bus.register_query(FindItem, lambda query: pytest.fail("handler should not run"))
    assert bus.send(FindItem(item_id="42")) == "cached"


def test_bus_rejects_non_application_message() -> None:
    with pytest.raises(TypeError):
        MessageBus().send("invalid")  # type: ignore[arg-type]
