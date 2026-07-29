"""
PROJECT SARATHI

Diagnostic Check Contract

Defines the stable extension point implemented by every
Framework Doctor diagnostic check.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .result import DiagnosticResult


class DiagnosticCheck(ABC):
    """Define the contract for a framework diagnostic check."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable unique check name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a concise description of the check."""

    @abstractmethod
    def run(self) -> DiagnosticResult:
        """Execute the check and return its typed result."""
