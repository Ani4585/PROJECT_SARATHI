"""Tests for PROJECT SARATHI built-in diagnostics."""

from __future__ import annotations

import pytest

from src.observability import (
    DiagnosticStatus,
    ModuleImportCheck,
    PythonRuntimeCheck,
    VersionMetadataCheck,
    create_default_checks,
    create_framework_doctor,
)


def test_runtime_check_passes_supported_cpython() -> None:
    result = PythonRuntimeCheck(
        minimum_version=(3, 14),
        runtime_version=(3, 14, 6),
        implementation="CPython",
    ).run()

    assert result.status is DiagnosticStatus.PASS
    assert result.details == (
        "Minimum: Python 3.14",
        "Detected: CPython 3.14.6",
    )


def test_runtime_check_fails_unsupported_version() -> None:
    result = PythonRuntimeCheck(
        minimum_version=(3, 14),
        runtime_version=(3, 13, 9),
        implementation="CPython",
    ).run()

    assert result.status is DiagnosticStatus.FAIL
    assert result.summary == (
        "The active Python version is unsupported."
    )


def test_runtime_check_warns_for_non_cpython() -> None:
    result = PythonRuntimeCheck(
        minimum_version=(3, 14),
        runtime_version=(3, 14, 6),
        implementation="PyPy",
    ).run()

    assert result.status is DiagnosticStatus.WARNING
    assert result.warning is True


def test_runtime_check_rejects_invalid_minimum() -> None:
    with pytest.raises(
        ValueError,
        match="exactly 2 parts",
    ):
        PythonRuntimeCheck(
            minimum_version=(3, 14, 0),
        )


def test_version_metadata_check_accepts_current_release() -> None:
    result = VersionMetadataCheck().run()

    assert result.status is DiagnosticStatus.PASS
    assert result.details == (
        "Framework: PROJECT SARATHI",
        "Version: 0.7.1",
        "Milestone: M12.2",
        "Build date: 2026-07-29",
    )


def test_version_metadata_check_reports_all_invalid_fields() -> None:
    result = VersionMetadataCheck(
        framework_name=" ",
        version="release-seven",
        milestone="Milestone 12",
        build_date="2026-02-30",
    ).run()

    assert result.status is DiagnosticStatus.FAIL
    assert result.details == (
        "FRAMEWORK_NAME must be a non-empty string.",
        "VERSION must use semantic version format.",
        "MILESTONE must use the M<number> format.",
        "BUILD_DATE must be a valid ISO date.",
    )


def test_import_check_runs_modules_in_order() -> None:
    imported: list[str] = []

    def importer(module_name: str) -> object:
        imported.append(module_name)
        return object()

    check = ModuleImportCheck(
        ("src.core", "src.container"),
        importer=importer,
    )

    result = check.run()

    assert imported == [
        "src.core",
        "src.container",
    ]
    assert result.status is DiagnosticStatus.PASS
    assert result.details == (
        "Modules checked: 2",
    )


def test_import_check_reports_import_failures() -> None:
    def importer(module_name: str) -> object:
        if module_name == "src.missing":
            raise ModuleNotFoundError(
                "missing dependency"
            )

        return object()

    result = ModuleImportCheck(
        ("src.core", "src.missing"),
        importer=importer,
    ).run()

    assert result.status is DiagnosticStatus.FAIL
    assert result.details == (
        (
            "src.missing: ModuleNotFoundError: "
            "missing dependency"
        ),
    )


def test_import_check_rejects_duplicate_modules() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate framework module",
    ):
        ModuleImportCheck(
            ("src.core", "src.core"),
        )


def test_default_doctor_is_healthy_and_deterministic() -> None:
    checks = create_default_checks()

    assert tuple(
        check.name
        for check in checks
    ) == (
        "python-runtime",
        "version-metadata",
        "framework-imports",
    )

    report = create_framework_doctor().run()

    assert report.healthy is True
    assert report.total_checks == 3
    assert report.passed_checks == 3
    assert report.warning_checks == 0
    assert report.failed_checks == 0
