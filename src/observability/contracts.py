"""Stable structural contracts for observability components."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ContextManager, Protocol


class MetricRecorder(Protocol):
    def increment(self, name: str, amount: float = 1.0, labels: Mapping[str, object] | None = None) -> float: ...
    def set_gauge(self, name: str, value: float, labels: Mapping[str, object] | None = None) -> float: ...
    def observe(self, name: str, value: float, labels: Mapping[str, object] | None = None) -> None: ...
    def timer(self, name: str, labels: Mapping[str, object] | None = None) -> ContextManager[None]: ...


class EventSink(Protocol):
    def publish(self, event: object) -> object: ...


class SpanTracer(Protocol):
    def span(self, name: str, attributes: Mapping[str, object] | None = None) -> ContextManager[object]: ...
