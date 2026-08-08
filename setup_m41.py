import os
from pathlib import Path

def write_file(path_str: str, content: str):
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"[CREATED/UPDATED] {path_str}")

METRICS_CODE = '''
import threading
from typing import Dict, List, Optional, Any

class Counter:
    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.value = 0.0
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0):
        if value < 0:
            raise ValueError("Counter cannot be decremented")
        with self._lock:
            self.value += value

class Gauge:
    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.value = 0.0
        self._lock = threading.Lock()

    def set(self, value: float):
        with self._lock:
            self.value = float(value)

    def inc(self, value: float = 1.0):
        with self._lock:
            self.value += value

    def dec(self, value: float = 1.0):
        with self._lock:
            self.value -= value

class Histogram:
    def __init__(self, name: str, description: str = "", buckets: Optional[List[float]] = None):
        self.name = name
        self.description = description
        self.buckets = sorted(buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        self.bucket_counts = {b: 0 for b in self.buckets}
        self.sum = 0.0
        self.count = 0
        self._lock = threading.Lock()

    def observe(self, value: float):
        with self._lock:
            self.sum += value
            self.count += 1
            for b in self.buckets:
                if value <= b:
                    self.bucket_counts[b] += 1

class PrometheusExporter:
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}

    def register_counter(self, counter: Counter):
        self.counters[counter.name] = counter

    def register_gauge(self, gauge: Gauge):
        self.gauges[gauge.name] = gauge

    def register_histogram(self, histogram: Histogram):
        self.histograms[histogram.name] = histogram

    def export(self) -> str:
        lines = []
        for name, c in self.counters.items():
            lines.append(f"# HELP {name} {c.description}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {c.value}")

        for name, g in self.gauges.items():
            lines.append(f"# HELP {name} {g.description}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {g.value}")

        for name, h in self.histograms.items():
            lines.append(f"# HELP {name} {h.description}")
            lines.append(f"# TYPE {name} histogram")
            for b, count in h.bucket_counts.items():
                lines.append(f'{name}_bucket{{le="{b}"}} {count}')
            lines.append(f'{name}_bucket{{le="+Inf"}} {h.count}')
            lines.append(f"{name}_sum {h.sum}")
            lines.append(f"{name}_count {h.count}")

        return "\\n".join(lines)
'''

TRACING_CODE = '''
import asyncio
import contextvars
import functools
import inspect
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Any

_ACTIVE_SPAN: contextvars.ContextVar[Optional['Span']] = contextvars.ContextVar('active_span', default=None)

@dataclass
class SpanContext:
    trace_id: str
    span_id: str
    trace_flags: str = "01"
    tracestate: str = ""

    def to_traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"

    @classmethod
    def from_traceparent(cls, traceparent: str) -> Optional['SpanContext']:
        try:
            parts = traceparent.strip().split('-')
            if len(parts) == 4 and parts[0] == "00":
                return cls(trace_id=parts[1], span_id=parts[2], trace_flags=parts[3])
        except Exception:
            pass
        return None

class Span:
    def __init__(self, name: str, tracer: 'Tracer', parent_context: Optional[SpanContext] = None):
        self.name = name
        self.tracer = tracer
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.status: str = "OK"
        self.error: Optional[Exception] = None

        trace_id = parent_context.trace_id if parent_context else uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        self.parent_span_id = parent_context.span_id if parent_context else None
        self.context = SpanContext(trace_id=trace_id, span_id=span_id)
        self._token = None

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })

    def record_exception(self, exc: Exception):
        self.status = "ERROR"
        self.error = exc
        self.add_event("exception", {"exception.type": type(exc).__name__, "exception.message": str(exc)})

    def __enter__(self):
        self._token = _ACTIVE_SPAN.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.record_exception(exc_val)
        self.end_time = time.time()
        if self._token:
            _ACTIVE_SPAN.reset(self._token)
        self.tracer.record_span(self)

class Tracer:
    def __init__(self, service_name: str = "sarathi_service"):
        self.service_name = service_name
        self.finished_spans: List[Span] = []

    def start_span(self, name: str, parent_context: Optional[SpanContext] = None) -> Span:
        if parent_context is None:
            active = _ACTIVE_SPAN.get()
            if active:
                parent_context = active.context
        return Span(name=name, tracer=self, parent_context=parent_context)

    def record_span(self, span: Span):
        self.finished_spans.append(span)

    def current_span(self) -> Optional[Span]:
        return _ACTIVE_SPAN.get()

def trace(tracer: Tracer, span_name: Optional[str] = None):
    def decorator(fn: Callable):
        name = span_name or fn.__name__
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                with tracer.start_span(name):
                    return await fn(*args, **kwargs)
            return wrapper
        else:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                with tracer.start_span(name):
                    return fn(*args, **kwargs)
            return wrapper
    return decorator
'''

EXPORTERS_CODE = '''
import json
from typing import List
from .tracing import Span

class InMemorySpanExporter:
    def __init__(self):
        self.spans: List[Span] = []

    def export(self, span: Span):
        self.spans.append(span)

class ConsoleSpanExporter:
    def export(self, span: Span):
        print(f"[SPAN EXPORT] Name: {span.name} | Trace ID: {span.context.trace_id} | Status: {span.status}")

class OTLPJSONExporter:
    def export(self, span: Span) -> str:
        data = {
            "name": span.name,
            "trace_id": span.context.trace_id,
            "span_id": span.context.span_id,
            "parent_span_id": span.parent_span_id,
            "status": span.status,
            "attributes": span.attributes,
            "events": span.events,
            "start_time": span.start_time,
            "end_time": span.end_time
        }
        return json.dumps(data)
'''

TELEMETRY_INIT_CODE = '''
from .metrics import Counter, Gauge, Histogram, PrometheusExporter
from .tracing import SpanContext, Span, Tracer, trace
from .exporters import InMemorySpanExporter, ConsoleSpanExporter, OTLPJSONExporter

__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "PrometheusExporter",
    "SpanContext",
    "Span",
    "Tracer",
    "trace",
    "InMemorySpanExporter",
    "ConsoleSpanExporter",
    "OTLPJSONExporter",
]
'''

TEST_M41_CODE = '''
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

@pytest.mark.asyncio
async def test_trace_decorator_async():
    tracer = Tracer("async_service")

    @trace(tracer, "async_operation")
    async def fetch_data():
        await asyncio.sleep(0.01)
        return "data"

    res = await fetch_data()
    assert res == "data"
    assert len(tracer.finished_spans) == 1
    assert tracer.finished_spans[0].name == "async_operation"
'''

targets = [
    ("src/sarathi/telemetry/metrics.py", METRICS_CODE),
    ("src/sarathi/telemetry/tracing.py", TRACING_CODE),
    ("src/sarathi/telemetry/exporters.py", EXPORTERS_CODE),
    ("src/sarathi/telemetry/__init__.py", TELEMETRY_INIT_CODE),
    ("sarathi/telemetry/metrics.py", METRICS_CODE),
    ("sarathi/telemetry/tracing.py", TRACING_CODE),
    ("sarathi/telemetry/exporters.py", EXPORTERS_CODE),
    ("sarathi/telemetry/__init__.py", TELEMETRY_INIT_CODE),
    ("tests/test_telemetry_m41.py", TEST_M41_CODE),
]

for rel_path, content in targets:
    write_file(rel_path, content)

for main_init in ["src/sarathi/__init__.py", "sarathi/__init__.py"]:
    p = Path(main_init)
    existing = p.read_text(encoding="utf-8") if p.exists() else ""
    if "telemetry" not in existing:
        p.write_text(existing + "\nfrom . import telemetry\n", encoding="utf-8")
        print(f"[UPDATED EXPORTS] {main_init}")

print("Milestone 41 setup completed successfully!")
