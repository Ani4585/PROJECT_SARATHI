"""
PROJECT SARATHI

Framework Version Tooling

Reads and validates framework version metadata from
the project's single source of truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from .filesystem import setup_project_root


setup_project_root()

from src.core.version import (
    BUILD_DATE,
    FRAMEWORK_NAME,
    MILESTONE,
    VERSION,
)


VERSION_PATTERN = re.compile(
    r"^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$"
)

MILESTONE_PATTERN = re.compile(
    r"^M\d+(?:\.\d+)?$"
)


@dataclass(frozen=True, slots=True)
class VersionInformation:
    """
    Immutable framework version metadata.
    """

    framework_name: str
    version: str
    milestone: str
    build_date: str

    def as_dict(
        self,
    ) -> dict[str, str]:
        """
        Return display-friendly version information.
        """

        return {
            "Name": self.framework_name,
            "Version": self.version,
            "Milestone": self.milestone,
            "Build Date": self.build_date,
        }


def get_version_information() -> VersionInformation:
    """
    Return current framework version information.
    """

    return VersionInformation(
        framework_name=FRAMEWORK_NAME,
        version=VERSION,
        milestone=MILESTONE,
        build_date=BUILD_DATE,
    )


def validate_framework_name(
    framework_name: str,
) -> bool:
    """
    Validate the framework name.
    """

    return bool(
        framework_name.strip()
    )


def validate_version(
    version: str,
) -> bool:
    """
    Validate semantic version formatting.
    """

    return (
        VERSION_PATTERN.fullmatch(
            version
        )
        is not None
    )


def validate_milestone(
    milestone: str,
) -> bool:
    """
    Validate milestone formatting.
    """

    return (
        MILESTONE_PATTERN.fullmatch(
            milestone
        )
        is not None
    )


def validate_build_date(
    build_date: str,
) -> bool:
    """
    Validate an ISO-formatted build date.
    """

    try:
        date.fromisoformat(
            build_date
        )

    except ValueError:
        return False

    return True


def validate_version_information(
    information: VersionInformation | None = None,
) -> dict[str, bool]:
    """
    Validate all framework version metadata.
    """

    if information is None:
        information = get_version_information()

    return {
        "Framework Name": validate_framework_name(
            information.framework_name
        ),
        "Version Format": validate_version(
            information.version
        ),
        "Milestone Format": validate_milestone(
            information.milestone
        ),
        "Build Date Format": validate_build_date(
            information.build_date
        ),
    }