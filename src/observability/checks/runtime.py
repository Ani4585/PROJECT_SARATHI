"""
PROJECT SARATHI

Python Runtime Diagnostic

Validates that the framework is executing on its supported
Python runtime.
"""

from __future__ import annotations

from platform import python_implementation
from sys import version_info

from ..check import DiagnosticCheck
from ..result import DiagnosticResult
from ..status import DiagnosticStatus


MINIMUM_PYTHON_VERSION = (3, 14)


class PythonRuntimeCheck(DiagnosticCheck):
    """Validate the active Python runtime."""

    def __init__(
        self,
        *,
        minimum_version: tuple[int, int] = (
            MINIMUM_PYTHON_VERSION
        ),
        runtime_version: tuple[int, int, int] | None = None,
        implementation: str | None = None,
    ) -> None:
        """Initialize the runtime diagnostic."""

        self._minimum_version = self._validate_version(
            minimum_version,
            expected_parts=2,
            label="Minimum Python version",
        )

        detected_version = (
            runtime_version
            if runtime_version is not None
            else (
                version_info.major,
                version_info.minor,
                version_info.micro,
            )
        )

        self._runtime_version = self._validate_version(
            detected_version,
            expected_parts=3,
            label="Runtime Python version",
        )

        detected_implementation = (
            implementation
            if implementation is not None
            else python_implementation()
        )

        if not isinstance(detected_implementation, str):
            raise TypeError(
                "Python implementation must be a string."
            )

        normalized_implementation = (
            detected_implementation.strip()
        )

        if not normalized_implementation:
            raise ValueError(
                "Python implementation must not be empty."
            )

        self._implementation = normalized_implementation

    @property
    def name(self) -> str:
        """Return the stable diagnostic name."""

        return "python-runtime"

    @property
    def description(self) -> str:
        """Return the diagnostic description."""

        return "Validate the active Python runtime."

    def run(self) -> DiagnosticResult:
        """Validate implementation and version compatibility."""

        required = ".".join(
            str(part)
            for part in self._minimum_version
        )
        detected = ".".join(
            str(part)
            for part in self._runtime_version
        )

        details = (
            f"Minimum: Python {required}",
            (
                "Detected: "
                f"{self._implementation} {detected}"
            ),
        )

        if (
            self._runtime_version[:2]
            < self._minimum_version
        ):
            return DiagnosticResult(
                name=self.name,
                status=DiagnosticStatus.FAIL,
                summary=(
                    "The active Python version is unsupported."
                ),
                details=details,
            )

        if self._implementation.casefold() != "cpython":
            return DiagnosticResult(
                name=self.name,
                status=DiagnosticStatus.WARNING,
                summary=(
                    "The Python version is supported, but the "
                    "runtime implementation is not CPython."
                ),
                details=details,
            )

        return DiagnosticResult(
            name=self.name,
            status=DiagnosticStatus.PASS,
            summary="The Python runtime is supported.",
            details=details,
        )

    @staticmethod
    def _validate_version(
        value: tuple[int, ...],
        *,
        expected_parts: int,
        label: str,
    ) -> tuple[int, ...]:
        """Validate and normalize a version tuple."""

        if not isinstance(value, tuple):
            raise TypeError(
                f"{label} must be a tuple."
            )

        if len(value) != expected_parts:
            raise ValueError(
                f"{label} must contain exactly "
                f"{expected_parts} parts."
            )

        if any(
            not isinstance(part, int)
            or isinstance(part, bool)
            or part < 0
            for part in value
        ):
            raise ValueError(
                f"{label} parts must be non-negative integers."
            )

        return value
