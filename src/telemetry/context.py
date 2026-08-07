import contextvars
import uuid
from typing import Optional, Dict, Any

_TRACE_ID_VAR: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)
_SPAN_ID_VAR: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("span_id", default=None)

class TraceContext:
    @staticmethod
    def get_trace_id() -> str:
        trace_id = _TRACE_ID_VAR.get()
        if not trace_id:
            trace_id = f"tr-{uuid.uuid4().hex[:16]}"
            _TRACE_ID_VAR.set(trace_id)
        return trace_id

    @staticmethod
    def get_span_id() -> str:
        span_id = _SPAN_ID_VAR.get()
        if not span_id:
            span_id = f"sp-{uuid.uuid4().hex[:8]}"
            _SPAN_ID_VAR.set(span_id)
        return span_id

    @staticmethod
    def set_context(trace_id: str, span_id: Optional[str] = None) -> None:
        _TRACE_ID_VAR.set(trace_id)
        _SPAN_ID_VAR.set(span_id or f"sp-{uuid.uuid4().hex[:8]}")

    @staticmethod
    def export_context() -> Dict[str, str]:
        return {
            "trace_id": TraceContext.get_trace_id(),
            "span_id": TraceContext.get_span_id(),
        }

    @staticmethod
    def reset() -> None:
        _TRACE_ID_VAR.set(None)
        _SPAN_ID_VAR.set(None)
