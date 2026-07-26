"""
PROJECT SARATHI

Application entry point.
"""

from __future__ import annotations

from src.application import ApplicationBuilder


def main() -> None:
    """
    Create and run the application.
    """

    app = (
        ApplicationBuilder()
        .build()
    )

    app.run()


if __name__ == "__main__":
    main()