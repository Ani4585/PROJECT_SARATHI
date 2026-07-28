"""
Tests for the PROJECT SARATHI repository tooling framework.
"""

from __future__ import annotations

from pathlib import Path

from scripts.tooling.filesystem import (
    PROJECT_ROOT,
    count_files,
    file_exists,
    required_file_status,
)

from scripts.tooling.git_tools import (
    collect_git_status,
)

from scripts.tooling.report import (
    CheckResult,
    ToolingReport,
)

from scripts.tooling.statistics import (
    collect_repository_statistics,
)

from scripts.tooling.version import (
    get_version_information,
    validate_version_information,
)


def test_check_result_records_status() -> None:
    """
    CheckResult should preserve its result information.
    """

    result = CheckResult(
        name="Example",
        passed=True,
        details="Completed",
    )

    assert result.name == "Example"
    assert result.passed is True
    assert result.details == "Completed"


def test_tooling_report_calculates_summary() -> None:
    """
    ToolingReport should calculate pass and failure totals.
    """

    report = ToolingReport(
        title="Example Report"
    )

    report.add(
        "First",
        True,
    )

    report.add(
        "Second",
        False,
        "Expected failure",
    )

    assert report.total_checks == 2
    assert report.passed_checks == 1
    assert report.failed_checks == 1
    assert report.passed is False
    assert report.failed is True

    failures = report.failures()

    assert len(failures) == 1
    assert failures[0].name == "Second"


def test_project_root_exists() -> None:
    """
    The tooling framework should resolve the repository root.
    """

    assert isinstance(
        PROJECT_ROOT,
        Path,
    )

    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()


def test_required_file_status() -> None:
    """
    Required-file verification should report existing files.
    """

    statuses = required_file_status(
        (
            "README.md",
            "src/core/version.py",
            "sarathi.py",
        )
    )

    assert statuses["README.md"] is True
    assert statuses["src/core/version.py"] is True
    assert statuses["sarathi.py"] is True


def test_file_exists_rejects_missing_file() -> None:
    """
    Missing repository files should return False.
    """

    assert file_exists(
        "this_file_should_not_exist.xyz"
    ) is False


def test_repository_statistics_are_non_negative() -> None:
    """
    Repository statistics should return valid non-negative totals.
    """

    statistics = collect_repository_statistics()

    for value in statistics.as_dict().values():
        assert value >= 0

    assert statistics.source_files > 0
    assert statistics.developer_scripts > 0
    assert statistics.automated_test_files > 0
    assert statistics.python_lines > 0


def test_python_source_count_is_positive() -> None:
    """
    The source package should contain Python files.
    """

    source_files = count_files(
        PROJECT_ROOT / "src",
        "*.py",
    )

    assert source_files > 0


def test_version_information_is_valid() -> None:
    """
    Framework metadata should satisfy all version rules.
    """

    information = get_version_information()
    validation = validate_version_information(
        information
    )

    assert information.framework_name == "PROJECT SARATHI"
    assert all(
        validation.values()
    )


def test_git_status_returns_structured_result() -> None:
    """
    Git inspection should always return a GitStatus object.
    """

    status = collect_git_status()

    assert isinstance(
        status.available,
        bool,
    )

    assert isinstance(
        status.modified_files,
        tuple,
    )

    assert isinstance(
        status.untracked_files,
        tuple,
    )

    assert status.changed_file_count >= 0