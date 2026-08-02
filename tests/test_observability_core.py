"""Tests for official M13 events, tracing, and exporters."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.observability import (
    DiagnosticEvent,
    DiagnosticEventPublisher,
    InMemoryEventExporter,
    InMemorySpanExporter,
    JsonMetricsExporter,
    NoOpEventPublisher,
    NoOpTracer,
    SpanStatus,
    Tracer,
)
from src.metrics import MetricsRegistry


def test_diagnostic_event_normalizes_attributes() -> None:
    event = DiagnosticEvent.create(
        " operation.completed ",
        {"zeta": 2, "alpha": 1},
        correlation_id="corr-1",
        clock=lambda: datetime(2026, 8, 2, tzinfo=timezone.utc),
    )
    assert event.name == "operation.completed"
    assert event.attributes == (("alpha", "1"), ("zeta", "2"))
    assert event.correlation_id == "corr-1"


def test_diagnostic_event_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        DiagnosticEvent.create("event", clock=lambda: datetime(2026, 8, 2))


def test_event_publisher_preserves_order_and_isolates_failure() -> None:
    calls: list[str] = []
    publisher = DiagnosticEventPublisher()
    publisher.subscribe(lambda event: calls.append("first"))

    def broken(event: DiagnosticEvent) -> None:
        del event
        raise RuntimeError("boom")

    publisher.subscribe(broken)
    publisher.subscribe(lambda event: calls.append("third"))
    report = publisher.publish(DiagnosticEvent.create("event"))
    assert calls == ["first", "third"]
    assert (report.attempted, report.delivered) == (3, 2)
    assert report.failures == ("RuntimeError: boom",)


def test_event_subscription_can_be_removed() -> None:
    calls: list[str] = []
    publisher = DiagnosticEventPublisher()
    unsubscribe = publisher.subscribe(lambda event: calls.append(event.name))
    unsubscribe()
    assert publisher.publish(DiagnosticEvent.create("event")).attempted == 0
    assert calls == []


def test_noop_event_publisher_discards_event() -> None:
    report = NoOpEventPublisher().publish(DiagnosticEvent.create("event"))
    assert report.passed is True
    assert report.attempted == 0


def test_tracer_nests_spans_with_shared_correlation() -> None:
    exporter = InMemorySpanExporter()
    identifiers = iter(("correlation", "root", "child"))
    readings = iter((0.0, 1.0, 2.0, 3.0))
    tracer = Tracer(exporter.export, clock=lambda: next(readings), identifier=lambda: next(identifiers))
    with tracer.span("root") as root:
        with tracer.span("child") as child:
            assert child.parent_span_id == root.span_id
            assert child.correlation_id == root.correlation_id
        assert tracer.current_context == root
    assert tracer.current_context is None
    child_record, root_record = exporter.snapshot()
    assert child_record.duration_seconds == 1.0
    assert root_record.duration_seconds == 3.0


def test_tracer_records_error_and_reraises() -> None:
    exporter = InMemorySpanExporter()
    readings = iter((5.0, 6.0))
    identifiers = iter(("correlation", "span"))
    tracer = Tracer(exporter.export, clock=lambda: next(readings), identifier=lambda: next(identifiers))
    with pytest.raises(RuntimeError):
        with tracer.span("failure"):
            raise RuntimeError("boom")
    record = exporter.snapshot()[0]
    assert record.status is SpanStatus.ERROR
    assert record.error == "RuntimeError: boom"


def test_tracer_isolates_exporter_failure() -> None:
    def broken_exporter(record) -> None:
        del record
        raise OSError("unavailable")

    readings = iter((0.0, 1.0))
    identifiers = iter(("correlation", "span"))
    tracer = Tracer(broken_exporter, clock=lambda: next(readings), identifier=lambda: next(identifiers))
    with tracer.span("operation"):
        pass


def test_noop_tracer_preserves_context_manager_contract() -> None:
    with NoOpTracer().span("operation") as context:
        assert context is None


def test_reference_event_and_metrics_exporters() -> None:
    events = InMemoryEventExporter()
    event = DiagnosticEvent.create("event")
    events.export(event)
    assert events.snapshot() == (event,)

    metrics = MetricsRegistry()
    metrics.increment("requests", labels={"method": "GET"})
    document = JsonMetricsExporter().export(metrics.snapshot())
    assert '"name": "requests"' in document
    assert '"method": "GET"' in document
