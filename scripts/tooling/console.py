"""
PROJECT SARATHI

Developer Tooling Console Utilities

Provides consistent terminal output for repository
verification, status reporting, and release management.
"""

from __future__ import annotations

SEPARATOR_WIDTH = 60


def print_header(
    title: str,
) -> None:
    """
    Print a standard PROJECT SARATHI header.
    """

    print("=" * SEPARATOR_WIDTH)
    print("PROJECT SARATHI")
    print(title)
    print("=" * SEPARATOR_WIDTH)


def print_section(
    title: str,
) -> None:
    """
    Print a section heading.
    """

    print()
    print(title)
    print("-" * len(title))


def print_key_value(
    key: str,
    value: object,
) -> None:
    """
    Print an aligned key-value pair.
    """

    print(
        f"{key:<25}: {value}"
    )


def print_result(
    name: str,
    passed: bool,
) -> None:
    """
    Print a standardized PASS or FAIL result.
    """

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print_key_value(
        name,
        status,
    )


def print_warning(
    message: str,
) -> None:
    """
    Print a standardized warning.
    """

    print(
        f"WARNING: {message}"
    )


def print_error(
    message: str,
) -> None:
    """
    Print a standardized error.
    """

    print(
        f"ERROR: {message}"
    )


def print_verdict(
    passed: bool,
    success_message: str = "READY FOR COMMIT",
    failure_message: str = "COMMIT BLOCKED",
) -> None:
    """
    Print the final tooling verdict.
    """

    print()
    print("=" * SEPARATOR_WIDTH)

    if passed:
        print(success_message)
    else:
        print(failure_message)

    print("=" * SEPARATOR_WIDTH)