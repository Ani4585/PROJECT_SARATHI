"""
PROJECT SARATHI

Project Status Command.
"""

from __future__ import annotations

from tooling import (
    collect_git_status,
    collect_repository_statistics,
    get_version_information,
    print_header,
    print_key_value,
    print_section,
    validate_version_information,
)


def main() -> int:
    """
    Display the current framework and repository status.
    """

    print_header(
        "Project Status"
    )

    version_information = (
        get_version_information()
    )

    print_section(
        "Framework"
    )

    for key, value in version_information.as_dict().items():

        print_key_value(
            key,
            value,
        )

    version_validation = (
        validate_version_information(
            version_information
        )
    )

    print_section(
        "Version Validation"
    )

    for key, passed in version_validation.items():

        print_key_value(
            key,
            "PASS" if passed else "FAIL",
        )

    repository_statistics = (
        collect_repository_statistics()
    )

    print_section(
        "Repository"
    )

    for key, value in repository_statistics.as_dict().items():

        print_key_value(
            key,
            value,
        )

    git_status = collect_git_status()

    print_section(
        "Git"
    )

    print_key_value(
        "Available",
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

    passed = (
        all(
            version_validation.values()
        )
        and git_status.available
    )

    return (
        0
        if passed
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())