"""Human-readable and machine-readable extension diagnostics."""

from __future__ import annotations

from typing import Any

from .model import ExtensionDiagnostics


def extension_diagnostics_to_dict(report: ExtensionDiagnostics) -> dict[str, Any]:
    return {
        "total_points": report.total_points,
        "total_registrations": report.total_registrations,
        "shadowed_registrations": report.shadowed_registrations,
        "points": [
            {
                "name": point.name,
                "contract": point.contract,
                "policy": point.policy.value,
                "registrations": point.registrations,
                "active_owners": list(point.active_owners),
                "shadowed_owners": list(point.shadowed_owners),
            }
            for point in report.points
        ],
    }


def render_extension_diagnostics(report: ExtensionDiagnostics) -> str:
    lines = [
        "PROJECT SARATHI Extension Diagnostics",
        "=====================================",
        f"Points: {report.total_points}",
        f"Registrations: {report.total_registrations}",
        f"Shadowed: {report.shadowed_registrations}",
    ]
    for point in report.points:
        active = ", ".join(point.active_owners) or "none"
        lines.extend(
            (
                "",
                f"[{point.policy.value.upper()}] {point.name}",
                f"  Contract: {point.contract}",
                f"  Active: {active}",
            )
        )
        if point.shadowed_owners:
            lines.append(f"  Shadowed: {', '.join(point.shadowed_owners)}")
    return "\n".join(lines)
