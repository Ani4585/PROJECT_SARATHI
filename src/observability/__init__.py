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

__all__ = [
    "DEFAULT_FRAMEWORK_MODULES",
    "MINIMUM_PYTHON_VERSION",
    "DiagnosticCheck",
    "DiagnosticReport",
    "DiagnosticReportRenderer",
    "DiagnosticResult",
    "DiagnosticStatus",
    "FrameworkDoctor",
    "ModuleImportCheck",
    "PythonRuntimeCheck",
    "VersionMetadataCheck",
    "create_default_checks",
    "create_framework_doctor",
    "render_diagnostic_report",
]
