"""Immutable metric identity and snapshot models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MetricKind(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    DISTRIBUTION = "distribution"
    HISTOGRAM = "histogram"


@dataclass(frozen=True, slots=True, order=True)
class MetricKey:
    """Uniquely identify a metric series by name and normalized labels."""

    name: str
    labels: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class MetricSample:
    """Represent one series in an immutable metrics snapshot."""

    key: MetricKey
    kind: MetricKind
    value: float
    count: int = 0
    minimum: float | None = None
    maximum: float | None = None
    buckets: tuple[tuple[float, int], ...] = ()


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Contain a deterministic point-in-time metrics view."""

    samples: tuple[MetricSample, ...]

    def find(self, name: str, labels: tuple[tuple[str, str], ...] = ()) -> MetricSample | None:
        key = MetricKey(name, labels)
        return next((sample for sample in self.samples if sample.key == key), None)
