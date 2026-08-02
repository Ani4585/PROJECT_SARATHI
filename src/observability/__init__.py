"""
PROJECT SARATHI

Framework Observability

Provides typed diagnostic contracts, built-in checks, reports,
rendering, and the Framework Doctor execution engine.
"""

from .check import DiagnosticCheck
from .checks import (
    DEFAULT_FRAMEWORK_MODULES,
    MINIMUM_PYTHON_VERSION,
    ModuleImportCheck,
    PythonRuntimeCheck,
    VersionMetadataCheck,
)
from .defaults import (
    create_default_checks,
    create_framework_doctor,
)
from .doctor import FrameworkDoctor
from .renderer import (
    DiagnosticReportRenderer,
    render_diagnostic_report,
)
from .report import DiagnosticReport
from .result import DiagnosticResult
from .status import DiagnosticStatus
from .contracts import EventSink, MetricRecorder, SpanTracer
from .events import DiagnosticEvent, DiagnosticEventPublisher, EventPublication, NoOpEventPublisher
from .exporters import InMemoryEventExporter, InMemorySpanExporter, JsonMetricsExporter, NoOpExporter
from .tracing import NoOpTracer, SpanContext, SpanRecord, SpanStatus, Tracer

__all__ = [
    "DEFAULT_FRAMEWORK_MODULES",
    "MINIMUM_PYTHON_VERSION",
    "DiagnosticCheck",
    "DiagnosticReport",
    "DiagnosticReportRenderer",
    "DiagnosticResult",
    "DiagnosticStatus",
    "DiagnosticEvent",
    "DiagnosticEventPublisher",
    "EventPublication",
    "EventSink",
    "FrameworkDoctor",
    "InMemorySpanExporter",
    "InMemoryEventExporter",
    "JsonMetricsExporter",
    "MetricRecorder",
    "ModuleImportCheck",
    "NoOpEventPublisher",
    "NoOpExporter",
    "NoOpTracer",
    "PythonRuntimeCheck",
    "SpanContext",
    "SpanRecord",
    "SpanStatus",
    "SpanTracer",
    "Tracer",
    "VersionMetadataCheck",
    "create_default_checks",
    "create_framework_doctor",
    "render_diagnostic_report",
]
