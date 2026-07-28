"""
PROJECT SARATHI

Developer CLI Entry Point

Provides the thin executable composition root for the PROJECT
SARATHI developer command-line interface.
"""

from __future__ import annotations

from collections.abc import Sequence

from scripts.tooling.cli import create_cli_application


def main(
    arguments: Sequence[str] | None = None,
) -> int:
    """Execute the PROJECT SARATHI developer CLI.

    Args:
        arguments: Optional command-line arguments. When omitted,
            arguments are read from the active process.

    Returns:
        The exit code returned by the selected command.
    """

    application = create_cli_application()

    return application.run(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
