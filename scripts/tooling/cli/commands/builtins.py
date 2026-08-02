"""
PROJECT SARATHI

Developer CLI Built-in Registration

Creates and explicitly registers every command supplied by the
PROJECT SARATHI developer tooling framework.
"""

from __future__ import annotations

from ..registry import CommandRegistry
from .audit import AuditCommand
from .benchmark import BenchmarkCommand
from .report import ReportCommand
from .plugins import PluginsCommand
from .monitor import MonitorCommand
from .diagnostics import DiagnosticsCommand
from .adr import AdrCommand
from .dashboard import DashboardCommand
from ..plugins import CliPluginLoader
from .compilation import CompilationCommand
from .coverage import CoverageCommand
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
    plugin_loader: CliPluginLoader | None = None,
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
        CoverageCommand()
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
        BenchmarkCommand()
    )
    registry.register(
        ReportCommand()
    )
    registry.register(
        PluginsCommand(plugin_loader or CliPluginLoader(lambda: ()))
    )
    registry.register(
        MonitorCommand()
    )
    registry.register(
        DiagnosticsCommand()
    )
    registry.register(
        AdrCommand()
    )
    registry.register(
        DashboardCommand()
    )
    registry.register(
        VerificationCommand(registry)
    )


def create_builtin_registry(plugin_loader: CliPluginLoader | None = None) -> CommandRegistry:
    """Create a registry containing all built-in commands.

    Returns:
        A fully configured command registry.
    """

    registry = CommandRegistry()
    resolved_plugin_loader = plugin_loader or CliPluginLoader()

    register_builtin_commands(
        registry,
        resolved_plugin_loader,
    )

    resolved_plugin_loader.load_into(registry)

    return registry
