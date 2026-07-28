"""
PROJECT SARATHI

Developer CLI Package

Provides the extensible command-line architecture used by
PROJECT SARATHI repository tooling.
"""

from .application import (
    CliApplication,
    create_cli_application,
)
from .command import Command
from .context import CommandContext
from .registry import (
    CommandAlreadyRegisteredError,
    CommandNotFoundError,
    CommandRegistry,
)

__all__ = [
    "CliApplication",
    "Command",
    "CommandAlreadyRegisteredError",
    "CommandContext",
    "CommandNotFoundError",
    "CommandRegistry",
    "create_cli_application",
]
