"""
PROJECT SARATHI

Diagnostic Report Model

Collects and summarizes typed Framework Doctor results.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .result import DiagnosticResult


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Represent one complete Framework Doctor execution."""

    title: str
    results: tuple[DiagnosticResult, ...]
    duration_seconds: float

    def __post_init__(self) -> None:
        """Validate and normalize report values."""

        if not isinstance(self.title, str):
            raise TypeError(
                "Diagnostic report title must be a string."
            )

        normalized_title = self.title.strip()

        if not normalized_title:
            raise ValueError(
                "Diagnostic report title must not be empty."
            )

        normalized_results = tuple(self.results)

        if not all(
            isinstance(result, DiagnosticResult)
            for result in normalized_results
        ):
            raise TypeError(
                "Diagnostic report results must contain "
                "DiagnosticResult instances."
            )

        duration = float(self.duration_seconds)

        if not isfinite(duration) or duration < 0:
            raise ValueError(
                "Diagnostic report duration must be a finite, "
                "non-negative number."
            )

        object.__setattr__(
            self,
            "title",
            normalized_title,
        )
        object.__setattr__(
            self,
            "results",
            normalized_results,
        )
        object.__setattr__(
            self,
            "duration_seconds",
            duration,
        )

    @property
    def healthy(self) -> bool:
        """Return whether the report contains no failed checks."""

        return self.failed_checks == 0

    @property
    def total_checks(self) -> int:
        """Return the total number of results."""

        return len(self.results)

    @property
    def passed_checks(self) -> int:
        """Return the number of passed checks."""

        return sum(
            1
            for result in self.results
            if result.passed
        )

    @property
    def warning_checks(self) -> int:
        """Return the number of warning results."""

        return sum(
            1
            for result in self.results
            if result.warning
        )

    @property
    def failed_checks(self) -> int:
        """Return the number of failed checks."""

        return sum(
            1
            for result in self.results
            if result.failed
        )

    def warnings(self) -> tuple[DiagnosticResult, ...]:
        """Return every warning result."""

        return tuple(
            result
            for result in self.results
            if result.warning
        )

    def failures(self) -> tuple[DiagnosticResult, ...]:
        """Return every failed result."""

        return tuple(
            result
            for result in self.results
            if result.failed
        )
