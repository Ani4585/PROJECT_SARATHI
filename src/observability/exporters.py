"""Reference in-memory and no-op observability exporters."""

from __future__ import annotations

import json
from threading import RLock

from src.metrics import MetricsSnapshot

from .events import DiagnosticEvent
from .tracing import SpanRecord


class InMemorySpanExporter:
    """Collect completed spans safely for diagnostics and tests."""

    def __init__(self) -> None:
        self._records: list[SpanRecord] = []
        self._lock = RLock()

    def export(self, record: SpanRecord) -> None:
        with self._lock:
            self._records.append(record)

    def snapshot(self) -> tuple[SpanRecord, ...]:
        with self._lock:
            return tuple(self._records)


class InMemoryEventExporter:
    """Collect diagnostic events safely for inspection."""

    def __init__(self) -> None:
        self._events: list[DiagnosticEvent] = []
        self._lock = RLock()

    def export(self, event: DiagnosticEvent) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> tuple[DiagnosticEvent, ...]:
        with self._lock:
            return tuple(self._events)


class JsonMetricsExporter:
    """Export an immutable metrics snapshot as deterministic JSON."""

    def export(self, snapshot: MetricsSnapshot) -> str:
        document = {
            "metrics": [
                {
                    "name": sample.key.name,
                    "labels": dict(sample.key.labels),
                    "kind": sample.kind.value,
                    "value": sample.value,
                    "count": sample.count,
                    "minimum": sample.minimum,
                    "maximum": sample.maximum,
                    "buckets": list(sample.buckets),
                }
                for sample in snapshot.samples
            ]
        }
        return json.dumps(document, indent=2, sort_keys=True)


class NoOpExporter:
    """Discard exported observability records."""

    def export(self, record: object) -> None:
        del record
