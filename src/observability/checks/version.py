"""
PROJECT SARATHI

Release Metadata Diagnostic

Validates the authoritative framework release metadata without
depending on repository tooling or the command-line interface.
"""

from __future__ import annotations

from datetime import date
from re import compile as compile_pattern

from src.core.version import (
    BUILD_DATE,
    FRAMEWORK_NAME,
    MILESTONE,
    VERSION,
)

from ..check import DiagnosticCheck
from ..result import DiagnosticResult
from ..status import DiagnosticStatus


VERSION_PATTERN = compile_pattern(
    r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?"
)
MILESTONE_PATTERN = compile_pattern(
    r"M\d+(?:\.\d+)?"
)


class VersionMetadataCheck(DiagnosticCheck):
    """Validate authoritative framework release metadata."""

    def __init__(
        self,
        *,
        framework_name: object = FRAMEWORK_NAME,
        version: object = VERSION,
        milestone: object = MILESTONE,
        build_date: object = BUILD_DATE,
    ) -> None:
        """Initialize the metadata diagnostic."""

        self._framework_name = framework_name
        self._version = version
        self._milestone = milestone
        self._build_date = build_date

    @property
    def name(self) -> str:
        """Return the stable diagnostic name."""

        return "version-metadata"

    @property
    def description(self) -> str:
        """Return the diagnostic description."""

        return "Validate authoritative release metadata."

    def run(self) -> DiagnosticResult:
        """Validate every authoritative metadata field."""

        issues: list[str] = []

        if not self._is_nonempty_text(
            self._framework_name
        ):
            issues.append(
                "FRAMEWORK_NAME must be a non-empty string."
            )

        if (
            not isinstance(self._version, str)
            or VERSION_PATTERN.fullmatch(
                self._version
            ) is None
        ):
            issues.append(
                "VERSION must use semantic version format."
            )

        if (
            not isinstance(self._milestone, str)
            or MILESTONE_PATTERN.fullmatch(
                self._milestone
            ) is None
        ):
            issues.append(
                "MILESTONE must use the M<number> format."
            )

        if not self._is_valid_date(self._build_date):
            issues.append(
                "BUILD_DATE must be a valid ISO date."
            )

        if issues:
            return DiagnosticResult(
                name=self.name,
                status=DiagnosticStatus.FAIL,
                summary="Release metadata is invalid.",
                details=tuple(issues),
            )

        return DiagnosticResult(
            name=self.name,
            status=DiagnosticStatus.PASS,
            summary="Release metadata is valid.",
            details=(
                f"Framework: {self._framework_name}",
                f"Version: {self._version}",
                f"Milestone: {self._milestone}",
                f"Build date: {self._build_date}",
            ),
        )

    @staticmethod
    def _is_nonempty_text(value: object) -> bool:
        """Return whether a value is non-empty text."""

        return (
            isinstance(value, str)
            and bool(value.strip())
        )

    @staticmethod
    def _is_valid_date(value: object) -> bool:
        """Return whether a value is a valid ISO date."""

        if not isinstance(value, str):
            return False

        try:
            date.fromisoformat(value)
        except ValueError:
            return False

        return True
