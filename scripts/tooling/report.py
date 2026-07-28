"""
PROJECT SARATHI

Developer Tooling Report Models

Provides structured results for verification,
health checks, and release decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CheckResult:
    """
    Represents the result of one tooling check.
    """

    name: str
    passed: bool
    details: str | None = None


@dataclass(slots=True)
class ToolingReport:
    """
    Collects and summarizes tooling check results.
    """

    title: str

    results: list[CheckResult] = field(
        default_factory=list
    )

    def add(
        self,
        name: str,
        passed: bool,
        details: str | None = None,
    ) -> CheckResult:
        """
        Add one check result to the report.
        """

        result = CheckResult(
            name=name,
            passed=passed,
            details=details,
        )

        self.results.append(
            result
        )

        return result

    @property
    def passed(self) -> bool:
        """
        Return whether every recorded check passed.
        """

        return all(
            result.passed
            for result in self.results
        )

    @property
    def failed(self) -> bool:
        """
        Return whether at least one check failed.
        """

        return not self.passed

    @property
    def total_checks(self) -> int:
        """
        Return the total number of checks.
        """

        return len(
            self.results
        )

    @property
    def passed_checks(self) -> int:
        """
        Return the number of successful checks.
        """

        return sum(
            1
            for result in self.results
            if result.passed
        )

    @property
    def failed_checks(self) -> int:
        """
        Return the number of failed checks.
        """

        return sum(
            1
            for result in self.results
            if not result.passed
        )

    def failures(
        self,
    ) -> tuple[CheckResult, ...]:
        """
        Return all failed checks.
        """

        return tuple(
            result
            for result in self.results
            if not result.passed
        )