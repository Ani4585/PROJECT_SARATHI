"""Public extension framework API."""

from .errors import (
    ExtensionConflictError,
    ExtensionError,
    ExtensionTypeError,
    UnknownExtensionPointError,
)
from .model import (
    ExtensionDiagnostics,
    ExtensionPoint,
    ExtensionPointDiagnostic,
    ExtensionPolicy,
    ExtensionRegistration,
)
from .registry import ExtensionRegistry
from .render import extension_diagnostics_to_dict, render_extension_diagnostics

__all__ = [
    "ExtensionConflictError",
    "ExtensionDiagnostics",
    "ExtensionError",
    "ExtensionPoint",
    "ExtensionPointDiagnostic",
    "ExtensionPolicy",
    "ExtensionRegistration",
    "ExtensionRegistry",
    "ExtensionTypeError",
    "UnknownExtensionPointError",
    "extension_diagnostics_to_dict",
    "render_extension_diagnostics",
]
