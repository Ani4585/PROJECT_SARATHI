"""
PROJECT SARATHI

Diagnostic Report Renderer

Converts typed diagnostic reports into deterministic plain text
without depending on terminal or command-line infrastructure.
"""

from __future__ import annotations

from .report import DiagnosticReport
from .result import DiagnosticResult


class DiagnosticReportRenderer:
    """Render diagnostic reports as deterministic plain text."""

    def render(
        self,
        report: DiagnosticReport,
    ) -> str:
        """Render a complete diagnostic report.

        Args:
            report: Typed diagnostic report to render.

        Returns:
            A newline-normalized plain-text representation.

        Raises:
            TypeError: If report is not a DiagnosticReport.
        """

        if not isinstance(report, DiagnosticReport):
            raise TypeError(
                "Diagnostic report renderer requires a "
                "DiagnosticReport."
            )

        sections = [
            self._render_header(report),
            *(
                self._render_result(result)
                for result in report.results
            ),
            self._render_summary(report),
        ]

        return "\n\n".join(sections)

    @staticmethod
    def _render_header(
        report: DiagnosticReport,
    ) -> str:
        """Render the report title and underline."""

        return "\n".join(
            (
                report.title,
                "=" * len(report.title),
            )
        )

    @staticmethod
    def _render_result(
        result: DiagnosticResult,
    ) -> str:
        """Render one diagnostic result."""

        lines = [
            (
                f"[{result.status.value.upper()}] "
                f"{result.name}"
            ),
            f"  {result.summary}",
        ]

        lines.extend(
            f"  - {detail}"
            for detail in result.details
        )

        return "\n".join(lines)

    @classmethod
    def _render_summary(
        cls,
        report: DiagnosticReport,
    ) -> str:
        """Render counts, health, and duration."""

        return "\n".join(
            (
                (
                    f"Summary: {report.passed_checks} passed | "
                    f"{report.warning_checks} warnings | "
                    f"{report.failed_checks} failed | "
                    f"{report.total_checks} total"
                ),
                f"Overall: {cls._overall_label(report)}",
                (
                    "Duration: "
                    f"{report.duration_seconds:.6f} seconds"
                ),
            )
        )

    @staticmethod
    def _overall_label(
        report: DiagnosticReport,
    ) -> str:
        """Return a stable overall health label."""

        if report.total_checks == 0:
            return "NO CHECKS"

        if report.failed_checks:
            return "UNHEALTHY"

        if report.warning_checks:
            return "HEALTHY WITH WARNINGS"

        return "HEALTHY"


def render_diagnostic_report(
    report: DiagnosticReport,
) -> str:
    """Render a report using the standard renderer."""

    return DiagnosticReportRenderer().render(report)
