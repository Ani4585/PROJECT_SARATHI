"""
PROJECT SARATHI

Diagnostic Status Model

Defines the stable outcome values used throughout the
framework observability system.
"""

from __future__ import annotations

from enum import Enum


class DiagnosticStatus(str, Enum):
    """Represent the outcome of one diagnostic check."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
