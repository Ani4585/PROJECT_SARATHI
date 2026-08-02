"""Nested tracing contexts, correlations, and failure-isolated export."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from uuid import uuid4


class SpanStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SpanContext:
    correlation_id: str
    span_id: str
    parent_span_id: str | None = None


@dataclass(frozen=True, slots=True)
class SpanRecord:
    name: str
    context: SpanContext
    duration_seconds: float
    status: SpanStatus
    attributes: tuple[tuple[str, str], ...] = ()
    error: str | None = None


_CURRENT_SPAN: ContextVar[SpanContext | None] = ContextVar("sarathi_current_span", default=None)


class Tracer:
    """Create correctly nested spans and export completed records."""

    def __init__(
        self,
        exporter: Callable[[SpanRecord], None] | None = None,
        clock: Callable[[], float] = perf_counter,
        identifier: Callable[[], str] = lambda: uuid4().hex,
    ) -> None:
        self._exporter = exporter or (lambda record: None)
        self._clock = clock
        self._identifier = identifier

    @property
    def current_context(self) -> SpanContext | None:
        return _CURRENT_SPAN.get()

    @contextmanager
    def span(self, name: str, attributes: Mapping[str, object] | None = None) -> Iterator[SpanContext]:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Span name must not be blank.")
        parent = _CURRENT_SPAN.get()
        context = SpanContext(
            correlation_id=parent.correlation_id if parent else self._identifier(),
            span_id=self._identifier(),
            parent_span_id=parent.span_id if parent else None,
        )
        token = _CURRENT_SPAN.set(context)
        started = self._clock()
        status = SpanStatus.OK
        error_text: str | None = None
        try:
            yield context
        except Exception as error:
            status = SpanStatus.ERROR
            error_text = f"{type(error).__name__}: {error}"
            raise
        finally:
            duration = max(0.0, self._clock() - started)
            _CURRENT_SPAN.reset(token)
            record = SpanRecord(
                normalized,
                context,
                duration,
                status,
                tuple(sorted((str(key).strip(), str(value)) for key, value in (attributes or {}).items())),
                error_text,
            )
            try:
                self._exporter(record)
            except Exception:
                pass


class NoOpTracer:
    """Provide a tracing context manager without recording spans."""

    @contextmanager
    def span(self, name: str, attributes: Mapping[str, object] | None = None) -> Iterator[None]:
        del name, attributes
        yield None
