"""HTTP Request lifecycle context, scope state tracking, and tracing."""

from __future__ import annotations

import asyncio
import contextvars
import time
import uuid
from typing import Any

from .contracts import ASGIScope

_trace_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_trace_id", default=None)
_span_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_span_id", default=None)


def current_trace_id() -> str | None:
    return _trace_id_ctx.get()


def current_span_id() -> str | None:
    return _span_id_ctx.get()


class RequestContext:
    """Encapsulates request lifecycle context, scoping, tracing, and timing."""

    def __init__(self, request: Any, scope: ASGIScope) -> None:
        from .middleware_builtins import current_request_id

        self._request = request
        self._scope = scope
        self._state: dict[str, Any] = dict(scope.get("state", {})) if isinstance(scope.get("state"), dict) else {}
        self._start_time = time.perf_counter()
        
        headers = getattr(request, "headers", None)
        header_req_id = headers.get("x-request-id") if headers else None
        context_req_id = current_request_id()
        self._request_id = header_req_id or context_req_id or str(uuid.uuid4())
        
        header_trace_id = headers.get("x-trace-id") if headers else None
        header_parent = headers.get("traceparent") if headers else None
        self._trace_id = header_trace_id or (header_parent.split("-")[1] if header_parent and len(header_parent.split("-")) >= 2 else str(uuid.uuid4()))
        self._span_id = str(uuid.uuid4())[:16]

        self.user: Any = None
        self.response: Any = None
        self._cancellation_event = asyncio.Event()
        self._finalized = False
        self._final_duration_ms: float | None = None

        # Set ContextVars for task context
        self._token_trace = _trace_id_ctx.set(self._trace_id)
        self._token_span = _span_id_ctx.set(self._span_id)

    @property
    def request(self) -> Any:
        return self._request

    @property
    def scope(self) -> ASGIScope:
        return self._scope

    @property
    def state(self) -> dict[str, Any]:
        return self._state

    @property
    def request_id(self) -> str:
        return self._request_id

    @property
    def trace_id(self) -> str:
        return self._trace_id

    @property
    def span_id(self) -> str:
        return self._span_id

    @property
    def start_time(self) -> float:
        return self._start_time

    @property
    def elapsed_ms(self) -> float:
        if self._final_duration_ms is not None:
            return self._final_duration_ms
        return (time.perf_counter() - self._start_time) * 1000.0

    @property
    def cancellation_event(self) -> asyncio.Event:
        return self._cancellation_event

    @property
    def is_cancelled(self) -> bool:
        return self._cancellation_event.is_set()

    @property
    def is_disconnected(self) -> bool:
        return self.is_cancelled

    @property
    def is_finalized(self) -> bool:
        return self._finalized

    def cancel(self) -> None:
        self._cancellation_event.set()

    def finalize_response(self, response: Any) -> Any:
        """Finalizes response state and injects tracking headers."""
        if self._finalized:
            return self.response
        self._finalized = True
        self._final_duration_ms = (time.perf_counter() - self._start_time) * 1000.0
        self.response = response

        if hasattr(response, "_headers") and hasattr(response._headers, "with_default"):
            response._headers = response._headers.with_default("x-request-id", self._request_id)
            response._headers = response._headers.with_default("x-trace-id", self._trace_id)
        return response

    def __getitem__(self, key: str) -> Any:
        return self._state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._state[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._state

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)


HttpContext = RequestContext
