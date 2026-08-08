import json
from typing import List, Dict, Any
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
