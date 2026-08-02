"""Public framework plugin foundation API."""

from .discovery import (
    DiscoveryStatus,
    DiscoveredPlugin,
    PluginDiscovery,
    PluginDiscoveryReport,
    compatibility_errors,
    manifest_from_mapping,
    render_discovery_report,
)
from .model import PluginContext, PluginManifest, PluginOperation, PluginReport, PluginState
from .plugin import Plugin
from .registry import PluginRegistry
from .registration import (
    DynamicRegistrationError,
    DynamicRegistrationManager,
    LateRegistrationError,
    RegistrationKind,
    RegistrationRecord,
    RegistrationScope,
    RegistrationState,
    UnloadFailure,
    UnloadReport,
)

__all__ = [
    "DiscoveredPlugin",
    "DiscoveryStatus",
    "DynamicRegistrationError",
    "DynamicRegistrationManager",
    "LateRegistrationError",
    "Plugin",
    "PluginContext",
    "PluginDiscovery",
    "PluginDiscoveryReport",
    "PluginManifest",
    "PluginOperation",
    "PluginRegistry",
    "PluginReport",
    "PluginState",
    "RegistrationKind",
    "RegistrationRecord",
    "RegistrationScope",
    "RegistrationState",
    "UnloadFailure",
    "UnloadReport",
    "compatibility_errors",
    "manifest_from_mapping",
    "render_discovery_report",
]
