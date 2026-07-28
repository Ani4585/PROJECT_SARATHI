"""
PROJECT SARATHI

Repository Health Check Command.
"""

from __future__ import annotations

from tooling import (
    ToolingReport,
    print_header,
    print_result,
    print_verdict,
    run_compilation,
    run_tests,
)


def main() -> int:
    """
    Run the repository health checks.
    """

    print_header(
        "Health Check"
    )

    report = ToolingReport(
        title="Repository Health Check"
    )

    test_result = run_tests(
        verbose=True
    )

    report.add(
        name="Unit Tests",
        passed=test_result.passed,
        details=(
            None
            if test_result.passed
            else f"Exit code {test_result.return_code}"
        ),
    )

    print_result(
        "Unit Tests",
        test_result.passed,
    )

    compilation_result = run_compilation()

    report.add(
        name="Compilation",
        passed=compilation_result.passed,
        details=(
            None
            if compilation_result.passed
            else f"Exit code {compilation_result.return_code}"
        ),
    )

    print_result(
        "Compilation",
        compilation_result.passed,
    )

    print_verdict(
        passed=report.passed,
        success_message="HEALTH CHECK PASSED",
        failure_message="HEALTH CHECK FAILED",
    )

    return (
        0
        if report.passed
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())