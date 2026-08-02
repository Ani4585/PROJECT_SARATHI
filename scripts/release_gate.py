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
    run_benchmarks,
    run_developer_report,
    run_cli_plugin_audit,
    run_health_monitoring,
    run_runtime_diagnostics,
    run_adr_validation,
    run_dashboard,
    run_coverage,
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
    "scripts/coverage_report.py",
    "scripts/tooling/coverage.py",
    "scripts/tooling/benchmark.py",
    "scripts/tooling/developer_report.py",
    "scripts/tooling/cli/plugins.py",
    "src/health/__init__.py",
    "src/runtime_diagnostics/__init__.py",
    "docs/adr/README.md",
    "scripts/tooling/dashboard.py",
    "config/benchmark_baselines.json",
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
        "Automated Tests and Coverage"
    )

    test_result = run_coverage()

    print_result(
        "Tests and Coverage",
        test_result.passed,
    )

    report.add(
        name="Tests and Coverage",
        passed=test_result.passed,
        details=(
            None
            if test_result.passed
            else f"Exit code {test_result.return_code}"
        ),
    )

    print_section(
        "Performance Regression"
    )

    benchmark_result = run_benchmarks()

    print_result(
        "Benchmarks",
        benchmark_result.passed,
    )

    report.add(
        name="Benchmarks",
        passed=benchmark_result.passed,
        details=(
            None
            if benchmark_result.passed
            else f"Exit code {benchmark_result.return_code}"
        ),
    )

    print_section(
        "Developer Environment"
    )

    developer_report_result = run_developer_report()

    print_result(
        "Dependency, Environment, and Tooling Reports",
        developer_report_result.passed,
    )

    report.add(
        name="Developer Reports",
        passed=developer_report_result.passed,
        details=(
            None
            if developer_report_result.passed
            else f"Exit code {developer_report_result.return_code}"
        ),
    )

    print_section(
        "CLI Extensions"
    )

    plugin_result = run_cli_plugin_audit()

    print_result(
        "CLI Plugin Discovery",
        plugin_result.passed,
    )

    report.add(
        name="CLI Plugin Discovery",
        passed=plugin_result.passed,
        details=(
            None
            if plugin_result.passed
            else f"Exit code {plugin_result.return_code}"
        ),
    )

    print_section(
        "Operational Health"
    )

    health_result = run_health_monitoring()

    print_result(
        "Liveness, Readiness, and Startup Health",
        health_result.passed,
    )

    report.add(
        name="Operational Health",
        passed=health_result.passed,
        details=(None if health_result.passed else f"Exit code {health_result.return_code}"),
    )

    print_section(
        "Runtime Diagnostics"
    )

    diagnostics_result = run_runtime_diagnostics()
    print_result("Safe-share Diagnostic Bundle", diagnostics_result.passed)
    report.add(
        name="Runtime Diagnostics",
        passed=diagnostics_result.passed,
        details=(None if diagnostics_result.passed else f"Exit code {diagnostics_result.return_code}"),
    )

    print_section("Architecture Decisions")
    adr_result = run_adr_validation()
    print_result("ADR Metadata and Links", adr_result.passed)
    report.add(
        name="Architecture Decisions",
        passed=adr_result.passed,
        details=(None if adr_result.passed else f"Exit code {adr_result.return_code}"),
    )

    print_section("Developer Dashboard")
    dashboard_result = run_dashboard()
    print_result("Dashboard and CI Summary", dashboard_result.passed)
    report.add(
        name="Developer Dashboard",
        passed=dashboard_result.passed,
        details=(None if dashboard_result.passed else f"Exit code {dashboard_result.return_code}"),
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
