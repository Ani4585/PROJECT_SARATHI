"""
PROJECT SARATHI

Compatibility exports for developer scripts.

New scripts should import directly from the
scripts.tooling package.
"""

from __future__ import annotations

from tooling import (
    PROJECT_ROOT,
    print_error,
    print_header,
    print_key_value,
    print_result,
    print_section,
    print_verdict,
    print_warning,
    setup_project_root,
)


__all__ = [
    "PROJECT_ROOT",
    "print_error",
    "print_header",
    "print_key_value",
    "print_result",
    "print_section",
    "print_verdict",
    "print_warning",
    "setup_project_root",
]