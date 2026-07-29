"""Tests for the PROJECT SARATHI observability foundation."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from src.observability import (
    DiagnosticCheck,
    DiagnosticReport,
    DiagnosticResult,
    DiagnosticStatus,
    FrameworkDoctor,
)


class StubCheck(DiagnosticCheck):
    """Provide a configurable diagnostic check for testing."""

    def __init__(
        self,
        name: str,
        status: DiagnosticStatus,
        *,
        events: list[str] | None = None,
    ) -> None:
        self._name = name
        self._status = status
        self._events = events

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Check {self.name}."

    def run(self) -> DiagnosticResult:
        if self._events is not None:
            self._events.append(self.name)

        return DiagnosticResult(
            name=self.name,
            status=self._status,
            summary=f"{self.name} completed.",
        )


class ExplodingCheck(DiagnosticCheck):
    """Provide a diagnostic check that raises an exception."""

    @property
    def name(self) -> str:
        return "exploding"

    @property
    def description(self) -> str:
        return "Raise a controlled test exception."

    def run(self) -> DiagnosticResult:
        raise RuntimeError("boom")


class MismatchedCheck(DiagnosticCheck):
    """Provide a check returning an invalid result name."""

    @property
    def name(self) -> str:
        return "expected"

    @property
    def description(self) -> str:
        return "Return a mismatched result."

    def run(self) -> DiagnosticResult:
        return DiagnosticResult(
            name="unexpected",
            status=DiagnosticStatus.PASS,
            summary="Incorrectly named result.",
        )


def create_clock(
    *values: float,
) -> Callable[[], float]:
    """Create a deterministic test clock."""

    iterator = iter(values)

    return lambda: next(iterator)


def test_diagnostic_status_values_are_stable() -> None:
    assert DiagnosticStatus.PASS.value == "pass"
    assert DiagnosticStatus.WARNING.value == "warning"
    assert DiagnosticStatus.FAIL.value == "fail"


def test_diagnostic_result_normalizes_text_and_details() -> None:
    result = DiagnosticResult(
        name="  version  ",
        status=DiagnosticStatus.WARNING,
        summary="  Version requires attention.  ",
        details=(
            "  Expected 0.7.0  ",
            "",
            "  Received 0.8.0  ",
        ),
    )

    assert result.name == "version"
    assert result.summary == "Version requires attention."
    assert result.details == (
        "Expected 0.7.0",
        "Received 0.8.0",
    )
    assert result.warning is True


def test_diagnostic_result_rejects_blank_name() -> None:
    with pytest.raises(
        ValueError,
        match="name must not be empty",
    ):
        DiagnosticResult(
            name=" ",
            status=DiagnosticStatus.PASS,
            summary="Valid summary.",
        )


def test_diagnostic_result_rejects_blank_summary() -> None:
    with pytest.raises(
        ValueError,
        match="summary must not be empty",
    ):
        DiagnosticResult(
            name="example",
            status=DiagnosticStatus.PASS,
            summary=" ",
        )


def test_diagnostic_report_calculates_summary() -> None:
    passed = DiagnosticResult(
        name="passed",
        status=DiagnosticStatus.PASS,
        summary="Passed.",
    )
    warning = DiagnosticResult(
        name="warning",
        status=DiagnosticStatus.WARNING,
        summary="Warning.",
    )
    failed = DiagnosticResult(
        name="failed",
        status=DiagnosticStatus.FAIL,
        summary="Failed.",
    )

    report = DiagnosticReport(
        title=" Test Report ",
        results=(passed, warning, failed),
        duration_seconds=0.25,
    )

    assert report.title == "Test Report"
    assert report.total_checks == 3
    assert report.passed_checks == 1
    assert report.warning_checks == 1
    assert report.failed_checks == 1
    assert report.healthy is False
    assert report.warnings() == (warning,)
    assert report.failures() == (failed,)


def test_diagnostic_report_rejects_negative_duration() -> None:
    with pytest.raises(
        ValueError,
        match="finite, non-negative",
    ):
        DiagnosticReport(
            title="Invalid Report",
            results=(),
            duration_seconds=-0.01,
        )


def test_doctor_runs_checks_in_order_and_records_duration() -> None:
    events: list[str] = []

    first = StubCheck(
        "first",
        DiagnosticStatus.PASS,
        events=events,
    )
    second = StubCheck(
        "second",
        DiagnosticStatus.WARNING,
        events=events,
    )

    doctor = FrameworkDoctor(
        (first, second),
        clock=create_clock(10.0, 10.125),
    )

    report = doctor.run()

    assert doctor.checks == (first, second)
    assert events == ["first", "second"]
    assert tuple(
        result.name
        for result in report.results
    ) == ("first", "second")
    assert report.duration_seconds == pytest.approx(0.125)
    assert report.healthy is True


def test_doctor_rejects_empty_check_collection() -> None:
    with pytest.raises(
        ValueError,
        match="at least one check",
    ):
        FrameworkDoctor(())


def test_doctor_rejects_duplicate_check_names() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate diagnostic check name",
    ):
        FrameworkDoctor(
            (
                StubCheck(
                    "duplicate",
                    DiagnosticStatus.PASS,
                ),
                StubCheck(
                    "duplicate",
                    DiagnosticStatus.FAIL,
                ),
            )
        )


def test_doctor_converts_check_exception_to_failure() -> None:
    report = FrameworkDoctor(
        (ExplodingCheck(),)
    ).run()

    result = report.results[0]

    assert report.healthy is False
    assert result.name == "exploding"
    assert result.status is DiagnosticStatus.FAIL
    assert result.details == (
        "RuntimeError: boom",
    )


def test_doctor_converts_mismatched_result_to_failure() -> None:
    report = FrameworkDoctor(
        (MismatchedCheck(),)
    ).run()

    result = report.results[0]

    assert result.name == "expected"
    assert result.status is DiagnosticStatus.FAIL
    assert result.details == (
        "Expected: expected",
        "Received: unexpected",
    )
