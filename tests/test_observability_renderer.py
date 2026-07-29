"""Tests for the PROJECT SARATHI diagnostic renderer."""

from __future__ import annotations

import pytest

from src.observability import (
    DiagnosticReport,
    DiagnosticReportRenderer,
    DiagnosticResult,
    DiagnosticStatus,
    render_diagnostic_report,
)


def create_result(
    name: str,
    status: DiagnosticStatus,
    *,
    summary: str | None = None,
    details: tuple[str, ...] = (),
) -> DiagnosticResult:
    """Create a diagnostic result for renderer tests."""

    return DiagnosticResult(
        name=name,
        status=status,
        summary=summary or f"{name} completed.",
        details=details,
    )


def create_report(
    *results: DiagnosticResult,
    title: str = "Diagnostic Report",
    duration_seconds: float = 0.0,
) -> DiagnosticReport:
    """Create a diagnostic report for renderer tests."""

    return DiagnosticReport(
        title=title,
        results=results,
        duration_seconds=duration_seconds,
    )


def test_renderer_produces_expected_plain_text() -> None:
    report = create_report(
        create_result(
            "python-runtime",
            DiagnosticStatus.PASS,
            summary="The Python runtime is supported.",
            details=("Detected: CPython 3.14.6",),
        ),
        title="Doctor Report",
        duration_seconds=0.125,
    )

    rendered = DiagnosticReportRenderer().render(report)

    assert rendered == "\n".join(
        (
            "Doctor Report",
            "=============",
            "",
            "[PASS] python-runtime",
            "  The Python runtime is supported.",
            "  - Detected: CPython 3.14.6",
            "",
            (
                "Summary: 1 passed | 0 warnings | "
                "0 failed | 1 total"
            ),
            "Overall: HEALTHY",
            "Duration: 0.125000 seconds",
        )
    )


def test_renderer_preserves_result_and_detail_order() -> None:
    report = create_report(
        create_result(
            "first",
            DiagnosticStatus.PASS,
            details=("first-a", "first-b"),
        ),
        create_result(
            "second",
            DiagnosticStatus.WARNING,
            details=("second-a",),
        ),
    )

    rendered = DiagnosticReportRenderer().render(report)

    assert rendered.index("[PASS] first") < rendered.index(
        "[WARNING] second"
    )
    assert rendered.index("first-a") < rendered.index(
        "first-b"
    )
    assert rendered.index("first-b") < rendered.index(
        "second-a"
    )


def test_renderer_reports_healthy_with_warnings() -> None:
    report = create_report(
        create_result(
            "optional-runtime",
            DiagnosticStatus.WARNING,
        )
    )

    rendered = DiagnosticReportRenderer().render(report)

    assert (
        "Summary: 0 passed | 1 warnings | "
        "0 failed | 1 total"
    ) in rendered
    assert "Overall: HEALTHY WITH WARNINGS" in rendered


def test_renderer_reports_unhealthy_failures() -> None:
    report = create_report(
        create_result(
            "runtime",
            DiagnosticStatus.PASS,
        ),
        create_result(
            "metadata",
            DiagnosticStatus.FAIL,
        ),
    )

    rendered = DiagnosticReportRenderer().render(report)

    assert (
        "Summary: 1 passed | 0 warnings | "
        "1 failed | 2 total"
    ) in rendered
    assert "Overall: UNHEALTHY" in rendered


def test_renderer_handles_empty_report() -> None:
    report = create_report(
        title="Empty Report",
        duration_seconds=0.5,
    )

    rendered = DiagnosticReportRenderer().render(report)

    assert rendered == "\n".join(
        (
            "Empty Report",
            "============",
            "",
            (
                "Summary: 0 passed | 0 warnings | "
                "0 failed | 0 total"
            ),
            "Overall: NO CHECKS",
            "Duration: 0.500000 seconds",
        )
    )


def test_renderer_rejects_invalid_report_type() -> None:
    with pytest.raises(
        TypeError,
        match="requires a DiagnosticReport",
    ):
        DiagnosticReportRenderer().render(object())


def test_standard_rendering_function_matches_renderer() -> None:
    report = create_report(
        create_result(
            "framework-imports",
            DiagnosticStatus.PASS,
        ),
        duration_seconds=0.000001,
    )

    assert render_diagnostic_report(report) == (
        DiagnosticReportRenderer().render(report)
    )
