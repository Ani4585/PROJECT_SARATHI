"""
PROJECT SARATHI

Framework Doctor Engine

Runs registered diagnostic checks in deterministic order and
returns a structured diagnostic report.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from time import perf_counter

from .check import DiagnosticCheck
from .report import DiagnosticReport
from .result import DiagnosticResult
from .status import DiagnosticStatus


class FrameworkDoctor:
    """Coordinate framework diagnostic checks."""

    def __init__(
        self,
        checks: Iterable[DiagnosticCheck],
        *,
        title: str = "PROJECT SARATHI Framework Doctor",
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        """Initialize the doctor with an ordered check collection.

        Args:
            checks: Diagnostic checks executed in supplied order.
            title: Title assigned to generated reports.
            clock: Monotonic clock used to measure execution time.

        Raises:
            TypeError: If a check or clock has an invalid type.
            ValueError: If checks are empty, unnamed, or duplicated.
        """

        normalized_checks = tuple(checks)

        if not normalized_checks:
            raise ValueError(
                "Framework Doctor requires at least one check."
            )

        if not callable(clock):
            raise TypeError(
                "Framework Doctor clock must be callable."
            )

        normalized_title = title.strip()

        if not normalized_title:
            raise ValueError(
                "Framework Doctor title must not be empty."
            )

        observed_names: set[str] = set()

        for check in normalized_checks:
            if not isinstance(check, DiagnosticCheck):
                raise TypeError(
                    "Framework Doctor checks must implement "
                    "DiagnosticCheck."
                )

            check_name = check.name

            if (
                not isinstance(check_name, str)
                or not check_name
                or check_name != check_name.strip()
            ):
                raise ValueError(
                    "Diagnostic check names must be non-empty "
                    "and contain no surrounding whitespace."
                )

            if check_name in observed_names:
                raise ValueError(
                    "Duplicate diagnostic check name: "
                    f"{check_name!r}."
                )

            observed_names.add(check_name)

        self._checks = normalized_checks
        self._title = normalized_title
        self._clock = clock

    @property
    def checks(self) -> tuple[DiagnosticCheck, ...]:
        """Return checks in deterministic execution order."""

        return self._checks

    def run(self) -> DiagnosticReport:
        """Execute every diagnostic check and build a report."""

        started_at = self._clock()

        results = tuple(
            self._run_check(check)
            for check in self.checks
        )

        finished_at = self._clock()

        return DiagnosticReport(
            title=self._title,
            results=results,
            duration_seconds=finished_at - started_at,
        )

    @staticmethod
    def _run_check(
        check: DiagnosticCheck,
    ) -> DiagnosticResult:
        """Execute one check without crashing the doctor."""

        try:
            result = check.run()
        except Exception as error:
            error_detail = (
                f"{type(error).__name__}: {error}"
                if str(error)
                else type(error).__name__
            )

            return DiagnosticResult(
                name=check.name,
                status=DiagnosticStatus.FAIL,
                summary=(
                    "Diagnostic check raised an unexpected "
                    "exception."
                ),
                details=(error_detail,),
            )

        if not isinstance(result, DiagnosticResult):
            return DiagnosticResult(
                name=check.name,
                status=DiagnosticStatus.FAIL,
                summary=(
                    "Diagnostic check returned an invalid "
                    "result type."
                ),
                details=(
                    f"Received: {type(result).__name__}",
                ),
            )

        if result.name != check.name:
            return DiagnosticResult(
                name=check.name,
                status=DiagnosticStatus.FAIL,
                summary=(
                    "Diagnostic check returned a mismatched "
                    "result name."
                ),
                details=(
                    f"Expected: {check.name}",
                    f"Received: {result.name}",
                ),
            )

        return result
