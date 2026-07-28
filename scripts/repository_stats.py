"""
PROJECT SARATHI

Repository Statistics Command.
"""

from __future__ import annotations

from tooling import (
    collect_repository_statistics,
    print_header,
    print_key_value,
)


def main() -> int:
    """
    Display current repository statistics.
    """

    print_header(
        "Repository Statistics"
    )

    statistics = (
        collect_repository_statistics()
    )

    for key, value in statistics.as_dict().items():

        print_key_value(
            key,
            value,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())