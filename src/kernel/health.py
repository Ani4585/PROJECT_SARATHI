"""Platform kernel health snapshot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KernelHealth:
    """Immutable operational summary for the integrated runtime."""

    framework: str
    version: str
    milestone: str
    state: str
    modules: tuple[str, ...]
    scheduled_jobs: int
    metric_series: int
