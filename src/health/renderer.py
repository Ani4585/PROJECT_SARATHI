"""Human-readable and machine-readable health reports."""

from __future__ import annotations

import json

from .model import HealthReport


class HealthTextRenderer:
    def render(self, report: HealthReport) -> str:
        lines = ["PROJECT SARATHI Health Report", "=" * 29]
        for result in report.results:
            lines.append(f"[{result.status.value.upper()}] {result.name}")
            lines.append(f"  {result.summary}")
            for detail in result.details:
                lines.append(f"  - {detail}")
        lines.extend(
            (
                "",
                f"Summary: {len(report.results)} checks | {report.duration_seconds:.6f} seconds",
                f"Overall: {report.status.value.upper()}",
            )
        )
        return "\n".join(lines)


class HealthJsonRenderer:
    def render(self, report: HealthReport) -> str:
        return json.dumps(report.to_dict(), indent=2)
