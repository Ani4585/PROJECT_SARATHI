"""Built-in exception, request identifier, and timing middleware."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from contextvars import ContextVar
from time import perf_counter
from typing import TypeAlias
from uuid import uuid4

from src.observability import MetricRecorder

from .middleware import HTTPResponse, MiddlewareResult, NextHandler
from .request import Request
from .response import Response, StreamingResponse, TextResponse


ErrorHandler: TypeAlias = Callable[[Request, Exception], MiddlewareResult]
_REQUEST_ID: ContextVar[str | None] = ContextVar(
    "sarathi_http_request_id", default=None
)


def current_request_id() -> str | None:
    """Return the identifier for the request executing in this async context."""

    return _REQUEST_ID.get()


async def _resolve(result: MiddlewareResult, source: str) -> HTTPResponse:
    if inspect.isawaitable(result):
        result = await result
    if not isinstance(result, (Response, StreamingResponse)):
        raise TypeError(f"{source} must return a Response or StreamingResponse.")
    return result


class ExceptionMiddleware:
    """Translate downstream failures into safe finite HTTP responses."""

    def __init__(
        self,
        handler: ErrorHandler | None = None,
        *,
        expose_errors: bool = False,
    ) -> None:
        if handler is not None and not callable(handler):
            raise TypeError("HTTP middleware exception handler must be callable.")
        self._handler = handler
        self._expose_errors = bool(expose_errors)

    async def __call__(self, request: Request, call_next: NextHandler) -> HTTPResponse:
        try:
            return await _resolve(call_next(request), "HTTP handler")
        except OSError:
            raise
        except Exception as error:
            if self._handler is not None:
                return await _resolve(
                    self._handler(request, error),
                    "HTTP middleware exception handler",
                )
            message = (
                f"{type(error).__name__}: {error}"
                if self._expose_errors
                else "Internal Server Error"
            )
            return TextResponse(message, status=500)


class RequestIdMiddleware:
    """Propagate or create a request identifier and return it to the client."""

    def __init__(
        self,
        *,
        header: str = "x-request-id",
        identifier: Callable[[], str] = lambda: uuid4().hex,
    ) -> None:
        if not isinstance(header, str) or not header.strip():
            raise ValueError("Request-ID header name must not be blank.")
        if not callable(identifier):
            raise TypeError("Request-ID generator must be callable.")
        self._header = header.strip()
        self._identifier = identifier

    async def __call__(self, request: Request, call_next: NextHandler) -> HTTPResponse:
        request_id = (request.headers.get(self._header) or "").strip()
        if not request_id:
            generated = self._identifier()
            if not isinstance(generated, str) or not generated.strip():
                raise ValueError("Request-ID generator must return a non-blank string.")
            request_id = generated.strip()
        token = _REQUEST_ID.set(request_id)
        try:
            response = await _resolve(call_next(request), "HTTP handler")
        finally:
            _REQUEST_ID.reset(token)
        return response.with_header(self._header, request_id)


class TimingMiddleware:
    """Measure downstream execution and expose server timing information."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = perf_counter,
        metrics: MetricRecorder | None = None,
        header: str = "server-timing",
        metric_name: str = "http.middleware.duration_seconds",
    ) -> None:
        if not callable(clock):
            raise TypeError("HTTP timing clock must be callable.")
        if not isinstance(header, str) or not header.strip():
            raise ValueError("HTTP timing header name must not be blank.")
        if not isinstance(metric_name, str) or not metric_name.strip():
            raise ValueError("HTTP timing metric name must not be blank.")
        self._clock = clock
        self._metrics = metrics
        self._header = header.strip()
        self._metric_name = metric_name.strip()

    async def __call__(self, request: Request, call_next: NextHandler) -> HTTPResponse:
        started = self._clock()
        outcome = "succeeded"
        elapsed: float | None = None
        try:
            response = await _resolve(call_next(request), "HTTP handler")
            elapsed = max(0.0, self._clock() - started)
            return response.with_header(
                self._header,
                f"app;dur={elapsed * 1000:.3f}",
            )
        except Exception:
            outcome = "failed"
            raise
        finally:
            if elapsed is None:
                elapsed = max(0.0, self._clock() - started)
            if self._metrics is not None:
                try:
                    self._metrics.observe(
                        self._metric_name,
                        elapsed,
                        labels={"method": request.method, "outcome": outcome},
                    )
                except Exception:
                    pass
