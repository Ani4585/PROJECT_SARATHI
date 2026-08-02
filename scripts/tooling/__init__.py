"""
PROJECT SARATHI

Repository Developer Tooling Framework.
"""

from .console import (
    print_error,
    print_header,
    print_key_value,
    print_result,
    print_section,
    print_verdict,
    print_warning,
)

from .filesystem import (
    EXCLUDED_DIRECTORIES,
    PROJECT_ROOT,
    count_files,
    directory_exists,
    file_exists,
    is_excluded,
    iter_files,
    required_file_status,
    setup_project_root,
)

from .git_tools import (
    GitStatus,
    collect_git_status,
    get_ahead_behind,
    get_current_branch,
    git_available,
)

from .report import (
    CheckResult,
    ToolingReport,
)

from .statistics import (
    RepositoryStatistics,
    collect_repository_statistics,
    count_python_lines,
)

from .verification import (
    CommandResult,
    all_required_files_exist,
    run_command,
    run_benchmarks,
    run_developer_report,
    run_cli_plugin_audit,
    run_health_monitoring,
    run_runtime_diagnostics,
    run_adr_validation,
    run_dashboard,
    run_compilation,
    run_coverage,
    run_tests,
    verify_required_files,
)

from .version import (
    VersionInformation,
    get_version_information,
    validate_build_date,
    validate_framework_name,
    validate_milestone,
    validate_version,
    validate_version_information,
)


__all__ = [
    "CheckResult",
    "CommandResult",
    "EXCLUDED_DIRECTORIES",
    "GitStatus",
    "PROJECT_ROOT",
    "RepositoryStatistics",
    "ToolingReport",
    "VersionInformation",
    "all_required_files_exist",
    "collect_git_status",
    "collect_repository_statistics",
    "count_files",
    "count_python_lines",
    "directory_exists",
    "file_exists",
    "get_ahead_behind",
    "get_current_branch",
    "get_version_information",
    "git_available",
    "is_excluded",
    "iter_files",
    "print_error",
    "print_header",
    "print_key_value",
    "print_result",
    "print_section",
    "print_verdict",
    "print_warning",
    "required_file_status",
    "run_command",
    "run_benchmarks",
    "run_developer_report",
    "run_cli_plugin_audit",
    "run_health_monitoring",
    "run_runtime_diagnostics",
    "run_adr_validation",
    "run_dashboard",
    "run_compilation",
    "run_coverage",
    "run_tests",
    "setup_project_root",
    "validate_build_date",
    "validate_framework_name",
    "validate_milestone",
    "validate_version",
    "validate_version_information",
    "verify_required_files",
]
