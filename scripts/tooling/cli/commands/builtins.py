"""
PROJECT SARATHI

Developer CLI Built-in Registration

Creates and explicitly registers every command supplied by the
PROJECT SARATHI developer tooling framework.
"""

from __future__ import annotations

from ..registry import CommandRegistry
from .audit import AuditCommand
from .compilation import CompilationCommand
from .doctor import DoctorCommand
from .script import ScriptCommand
from .testing import TestCommand
from .verification import VerificationCommand
from .version import VersionCommand


SCRIPT_COMMAND_DEFINITIONS = (
    (
        "stats",
        "Display repository statistics.",
        "scripts/repository_stats.py",
    ),
    (
        "status",
        "Display framework, repository, and Git status.",
        "scripts/project_status.py",
    ),
    (
        "health",
        "Run automated tests and compilation checks.",
        "scripts/health_check.py",
    ),
    (
        "release",
        "Run the release gate.",
        "scripts/release_gate.py",
    ),
)


def register_builtin_commands(
    registry: CommandRegistry,
) -> None:
    """Register all standard PROJECT SARATHI CLI commands.

    Args:
        registry: Registry that will receive the built-in commands.
    """

    for (
        name,
        description,
        script_path,
    ) in SCRIPT_COMMAND_DEFINITIONS:
        registry.register(
            ScriptCommand(
                name=name,
                description=description,
                script_path=script_path,
            )
        )

    registry.register(
        TestCommand()
    )
    registry.register(
        CompilationCommand()
    )
    registry.register(
        VersionCommand()
    )
    registry.register(
        DoctorCommand()
    )
    registry.register(
        AuditCommand()
    )
    registry.register(
        VerificationCommand(registry)
    )


def create_builtin_registry() -> CommandRegistry:
    """Create a registry containing all built-in commands.

    Returns:
        A fully configured command registry.
    """

    registry = CommandRegistry()

    register_builtin_commands(
        registry
    )

    return registry
