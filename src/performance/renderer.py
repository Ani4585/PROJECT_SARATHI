"""Performance snapshot and comparison reports."""

from __future__ import annotations

import json

from .model import PerformanceComparison, PerformanceSnapshot


class PerformanceTextRenderer:
    def render_snapshot(self, snapshot: PerformanceSnapshot) -> str:
        lines = [
            f"Performance: {snapshot.name}",
            f"Status: {snapshot.status.value.upper()}",
            f"Duration: {snapshot.duration_seconds:.6f} seconds",
            f"CPU: {snapshot.cpu_seconds:.6f} seconds",
            f"Peak memory: {snapshot.peak_memory_bytes} bytes",
        ]
        if snapshot.violations:
            lines.append("Budget violations: " + ", ".join(snapshot.violations))
        return "\n".join(lines)

    def render_comparison(self, comparison: PerformanceComparison) -> str:
        def show(value: float | None) -> str:
            return "n/a" if value is None else f"{value:+.2f}%"

        return "\n".join(
            (
                f"Performance comparison: {comparison.current.name}",
                f"Duration change: {show(comparison.duration_change_percent)}",
                f"CPU change: {show(comparison.cpu_change_percent)}",
                f"Peak memory change: {show(comparison.memory_change_percent)}",
            )
        )


class PerformanceJsonRenderer:
    def render_snapshot(self, snapshot: PerformanceSnapshot) -> str:
        return json.dumps(snapshot.to_dict(), indent=2)

    def render_comparison(self, comparison: PerformanceComparison) -> str:
        return json.dumps(comparison.to_dict(), indent=2)
