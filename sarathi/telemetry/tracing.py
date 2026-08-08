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
