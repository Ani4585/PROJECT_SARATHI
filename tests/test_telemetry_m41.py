import asyncio
import pytest
from sarathi.telemetry import (
    Counter,
    Gauge,
    Histogram,
    PrometheusExporter,
    SpanContext,
    Span,
    Tracer,
    trace,
)

def test_counter_inc():
    c = Counter("test_counter", "Test Description")
    c.inc(5)
    assert c.value == 5.0
    with pytest.raises(ValueError):
        c.inc(-1)

def test_gauge_set_inc_dec():
    g = Gauge("test_gauge", "Gauge Description")
    g.set(10)
    assert g.value == 10.0
    g.inc(2)
    assert g.value == 12.0
    g.dec(4)
    assert g.value == 8.0

def test_prometheus_exporter_output():
    exporter = PrometheusExporter()
    c = Counter("http_requests_total", "Total Requests")
    c.inc(10)
    exporter.register_counter(c)

    g = Gauge("active_tasks", "Active Background Tasks")
    g.set(3)
    exporter.register_gauge(g)

    output = exporter.export()
    assert "# TYPE http_requests_total counter" in output
    assert "http_requests_total 10.0" in output
    assert "active_tasks 3.0" in output

def test_w3c_traceparent_parsing():
    ctx = SpanContext(trace_id="4bf92f3577b34da6a3ce929d0e0e4736", span_id="00f067aa0ba902b7")
    header = ctx.to_traceparent()
    assert header == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

    parsed = SpanContext.from_traceparent(header)
    assert parsed is not None
    assert parsed.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed.span_id == "00f067aa0ba902b7"

def test_parent_child_span_linkage():
    tracer = Tracer("test_service")
    with tracer.start_span("root") as root:
        root.set_attribute("env", "prod")
        with tracer.start_span("child") as child:
            child.set_attribute("db", "postgres")

    assert len(tracer.finished_spans) == 2
    child_span = tracer.finished_spans[0]
    root_span = tracer.finished_spans[1]

    assert child_span.context.trace_id == root_span.context.trace_id
    assert child_span.parent_span_id == root_span.context.span_id

def test_trace_decorator_async():
    async def _test():
        tracer = Tracer("async_service")

        @trace(tracer, "async_operation")
        async def fetch_data():
            await asyncio.sleep(0.01)
            return "data"

        res = await fetch_data()
        assert res == "data"
        assert len(tracer.finished_spans) == 1
        assert tracer.finished_spans[0].name == "async_operation"

    asyncio.run(_test())
