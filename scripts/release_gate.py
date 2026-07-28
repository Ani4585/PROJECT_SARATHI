"""
PROJECT SARATHI

Release Gate Command

Runs all verification required before a repository commit.
"""

from __future__ import annotations

from tooling import (
    ToolingReport,
    collect_git_status,
    get_version_information,
    print_header,
    print_key_value,
    print_result,
    print_section,
    print_verdict,
    run_compilation,
    run_tests,
    validate_version_information,
    verify_required_files,
)


REQUIRED_FILES = (
    "README.md",
    "docs/STATUS.md",
    "docs/CHANGELOG.md",
    "docs/RELEASE_GATE.md",
    "src/core/version.py",
    "sarathi.py",
    "docs/milestones/M11_5_REPOSITORY_TOOLING.md",
    "scripts/health_check.py",
    "scripts/project_status.py",
    "scripts/repository_stats.py",
    "scripts/release_gate.py",
    "scripts/tooling/__init__.py",
    "scripts/tooling/console.py",
    "scripts/tooling/filesystem.py",
    "scripts/tooling/git_tools.py",
    "scripts/tooling/report.py",
    "scripts/tooling/statistics.py",
    "scripts/tooling/verification.py",
    "scripts/tooling/version.py",
)


def main() -> int:
    """
    Execute the complete repository release gate.
    """

    print_header(
        "RELEASE GATE"
    )

    report = ToolingReport(
        title="Release Gate"
    )

    print_section(
        "Version Metadata"
    )

    version_information = (
        get_version_information()
    )

    for key, value in version_information.as_dict().items():

        print_key_value(
            key,
            value,
        )

    version_results = (
        validate_version_information(
            version_information
        )
    )

    for name, passed in version_results.items():

        print_result(
            name,
            passed,
        )

        report.add(
            name=name,
            passed=passed,
        )

    print_section(
        "Required Files"
    )

    required_file_results = (
        verify_required_files(
            REQUIRED_FILES
        )
    )

    for path, exists in required_file_results.items():

        print_result(
            path,
            exists,
        )

        report.add(
            name=f"Required File: {path}",
            passed=exists,
        )

    print_section(
        "Automated Tests"
    )

    test_result = run_tests(
        verbose=True
    )

    print_result(
        "Unit Tests",
        test_result.passed,
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

    print_section(
        "Compilation"
    )

    compilation_result = run_compilation()

    print_result(
        "Compilation",
        compilation_result.passed,
    )

    report.add(
        name="Compilation",
        passed=compilation_result.passed,
        details=(
            None
            if compilation_result.passed
            else f"Exit code {compilation_result.return_code}"
        ),
    )

    print_section(
        "Git Repository"
    )

    git_status = collect_git_status()

    print_result(
        "Git Available",
        git_status.available,
    )

    print_key_value(
        "Branch",
        git_status.branch or "Unknown",
    )

    print_key_value(
        "Modified Files",
        len(git_status.modified_files),
    )

    print_key_value(
        "Added Files",
        len(git_status.added_files),
    )

    print_key_value(
        "Deleted Files",
        len(git_status.deleted_files),
    )

    print_key_value(
        "Renamed Files",
        len(git_status.renamed_files),
    )

    print_key_value(
        "Untracked Files",
        len(git_status.untracked_files),
    )

    print_key_value(
        "Changed Files",
        git_status.changed_file_count,
    )

    print_key_value(
        "Ahead",
        git_status.ahead,
    )

    print_key_value(
        "Behind",
        git_status.behind,
    )

    print_key_value(
        "Working Tree",
        (
            "DIRTY"
            if git_status.dirty
            else "CLEAN"
        ),
    )

    report.add(
        name="Git Repository",
        passed=git_status.available,
    )

    print_section(
        "Summary"
    )

    print_key_value(
        "Total Checks",
        report.total_checks,
    )

    print_key_value(
        "Passed Checks",
        report.passed_checks,
    )

    print_key_value(
        "Failed Checks",
        report.failed_checks,
    )

    if report.failed:

        print_section(
            "Failures"
        )

        for failure in report.failures():

            details = (
                failure.details
                or "No additional details"
            )

            print_key_value(
                failure.name,
                details,
            )

    print_verdict(
        passed=report.passed,
        success_message="READY FOR COMMIT",
        failure_message="COMMIT BLOCKED",
    )

    return (
        0
        if report.passed
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())