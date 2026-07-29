"""
PROJECT SARATHI

Diagnostic Result Model

Provides the immutable result produced by one framework
diagnostic check.
"""

from __future__ import annotations

from dataclasses import dataclass

from .status import DiagnosticStatus


@dataclass(frozen=True, slots=True)
class DiagnosticResult:
    """Represent the result of one diagnostic check.

    Attributes:
        name: Stable unique name of the diagnostic check.
        status: Outcome reported by the check.
        summary: Concise human-readable result description.
        details: Optional supporting diagnostic information.
    """

    name: str
    status: DiagnosticStatus
    summary: str
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate and normalize result values."""

        if not isinstance(self.name, str):
            raise TypeError(
                "Diagnostic result name must be a string."
            )

        if not isinstance(self.summary, str):
            raise TypeError(
                "Diagnostic result summary must be a string."
            )

        if not isinstance(self.status, DiagnosticStatus):
            raise TypeError(
                "Diagnostic result status must be "
                "a DiagnosticStatus value."
            )

        normalized_name = self.name.strip()
        normalized_summary = self.summary.strip()

        if not normalized_name:
            raise ValueError(
                "Diagnostic result name must not be empty."
            )

        if not normalized_summary:
            raise ValueError(
                "Diagnostic result summary must not be empty."
            )

        normalized_details: list[str] = []

        for detail in self.details:
            if not isinstance(detail, str):
                raise TypeError(
                    "Diagnostic result details must be strings."
                )

            normalized_detail = detail.strip()

            if normalized_detail:
                normalized_details.append(
                    normalized_detail
                )

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "summary",
            normalized_summary,
        )
        object.__setattr__(
            self,
            "details",
            tuple(normalized_details),
        )

    @property
    def passed(self) -> bool:
        """Return whether the check passed."""

        return self.status is DiagnosticStatus.PASS

    @property
    def warning(self) -> bool:
        """Return whether the check produced a warning."""

        return self.status is DiagnosticStatus.WARNING

    @property
    def failed(self) -> bool:
        """Return whether the check failed."""

        return self.status is DiagnosticStatus.FAIL
