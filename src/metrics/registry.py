"""Thread-safe in-process metrics registry."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock
from time import perf_counter

from .model import MetricKey, MetricKind, MetricSample, MetricsSnapshot


@dataclass(slots=True)
class _Distribution:
    count: int = 0
    total: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def observe(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)


def _key(name: str, labels: Mapping[str, object] | None = None) -> MetricKey:
    normalized = name.strip()
    if not normalized:
        raise ValueError("Metric name must not be blank.")
    if any(character.isspace() for character in normalized):
        raise ValueError("Metric names must not contain whitespace.")
    normalized_labels = tuple(
        sorted((str(key).strip(), str(value)) for key, value in (labels or {}).items())
    )
    if any(not label for label, _ in normalized_labels):
        raise ValueError("Metric label names must not be blank.")
    return MetricKey(normalized, normalized_labels)


class MetricsRegistry:
    """Record counters, gauges, distributions, and timings safely."""

    def __init__(self, clock: Callable[[], float] = perf_counter) -> None:
        self._clock = clock
        self._counters: dict[MetricKey, float] = {}
        self._gauges: dict[MetricKey, float] = {}
        self._distributions: dict[MetricKey, _Distribution] = {}
        self._lock = RLock()

    def increment(
        self,
        name: str,
        amount: float = 1.0,
        labels: Mapping[str, object] | None = None,
    ) -> float:
        numeric = float(amount)
        if numeric < 0:
            raise ValueError("Counter increments must not be negative.")
        key = _key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + numeric
            return self._counters[key]

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Mapping[str, object] | None = None,
    ) -> float:
        key = _key(name, labels)
        numeric = float(value)
        with self._lock:
            self._gauges[key] = numeric
        return numeric

    def observe(
        self,
        name: str,
        value: float,
        labels: Mapping[str, object] | None = None,
    ) -> None:
        key = _key(name, labels)
        numeric = float(value)
        with self._lock:
            self._distributions.setdefault(key, _Distribution()).observe(numeric)

    @contextmanager
    def timer(
        self,
        name: str,
        labels: Mapping[str, object] | None = None,
    ) -> Iterator[None]:
        """Measure elapsed seconds even when the timed block raises."""

        started = self._clock()
        try:
            yield
        finally:
            self.observe(name, self._clock() - started, labels)

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            samples = [
                MetricSample(key, MetricKind.COUNTER, value)
                for key, value in self._counters.items()
            ]
            samples.extend(
                MetricSample(key, MetricKind.GAUGE, value)
                for key, value in self._gauges.items()
            )
            samples.extend(
                MetricSample(
                    key,
                    MetricKind.DISTRIBUTION,
                    value=distribution.total,
                    count=distribution.count,
                    minimum=distribution.minimum,
                    maximum=distribution.maximum,
                )
                for key, distribution in self._distributions.items()
            )
        return MetricsSnapshot(tuple(sorted(samples, key=lambda sample: (sample.key, sample.kind.value))))

    def clear(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._distributions.clear()
