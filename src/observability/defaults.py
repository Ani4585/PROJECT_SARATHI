"""
PROJECT SARATHI

Default Framework Doctor Composition

Provides the standard diagnostic collection and Framework
Doctor used by applications and future CLI adapters.
"""

from __future__ import annotations

from .check import DiagnosticCheck
from .checks import (
    ModuleImportCheck,
    PythonRuntimeCheck,
    VersionMetadataCheck,
)
from .doctor import FrameworkDoctor


def create_default_checks(
) -> tuple[DiagnosticCheck, ...]:
    """Create checks in deterministic execution order."""

    return (
        PythonRuntimeCheck(),
        VersionMetadataCheck(),
        ModuleImportCheck(),
    )


def create_framework_doctor(
    *,
    title: str = "PROJECT SARATHI Framework Doctor",
) -> FrameworkDoctor:
    """Create the standard Framework Doctor."""

    return FrameworkDoctor(
        create_default_checks(),
        title=title,
    )
