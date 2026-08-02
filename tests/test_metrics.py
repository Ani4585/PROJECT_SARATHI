"""Tests for the in-process metrics component used by official M13."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from src.metrics import MetricKind, MetricsRegistry, NoOpMetricsRegistry


def test_counter_increments_and_returns_current_value() -> None:
    metrics = MetricsRegistry()
    assert metrics.increment("requests") == 1.0
    assert metrics.increment("requests", 2) == 3.0
    sample = metrics.snapshot().find("requests")
    assert sample is not None
    assert sample.kind is MetricKind.COUNTER
    assert sample.value == 3.0


def test_counter_rejects_negative_increment() -> None:
    with pytest.raises(ValueError):
        MetricsRegistry().increment("requests", -1)


def test_gauge_can_move_in_both_directions() -> None:
    metrics = MetricsRegistry()
    metrics.set_gauge("queue.depth", 10)
    metrics.set_gauge("queue.depth", 3)
    assert metrics.snapshot().find("queue.depth").value == 3.0  # type: ignore[union-attr]


def test_distribution_records_count_total_minimum_and_maximum() -> None:
    metrics = MetricsRegistry()
    for value in (3, 1, 5):
        metrics.observe("payload.size", value)
    sample = metrics.snapshot().find("payload.size")
    assert sample is not None
    assert sample.kind is MetricKind.DISTRIBUTION
    assert (sample.count, sample.value, sample.minimum, sample.maximum) == (3, 9.0, 1.0, 5.0)


def test_labels_are_normalized_in_sorted_order() -> None:
    metrics = MetricsRegistry()
    metrics.increment("requests", labels={"zone": "south", "method": "GET"})
    sample = metrics.snapshot().samples[0]
    assert sample.key.labels == (("method", "GET"), ("zone", "south"))


def test_different_labels_create_different_series() -> None:
    metrics = MetricsRegistry()
    metrics.increment("requests", labels={"status": 200})
    metrics.increment("requests", labels={"status": 500})
    assert len(metrics.snapshot().samples) == 2


def test_metric_name_must_be_nonblank_without_whitespace() -> None:
    with pytest.raises(ValueError):
        MetricsRegistry().increment(" ")
    with pytest.raises(ValueError):
        MetricsRegistry().increment("bad name")


def test_timer_records_elapsed_seconds() -> None:
    readings = iter((10.0, 10.25))
    metrics = MetricsRegistry(clock=lambda: next(readings))
    with metrics.timer("operation.duration"):
        pass
    sample = metrics.snapshot().find("operation.duration")
    assert sample is not None
    assert sample.value == 0.25
    assert sample.count == 1


def test_timer_records_elapsed_time_when_block_raises() -> None:
    readings = iter((5.0, 6.0))
    metrics = MetricsRegistry(clock=lambda: next(readings))
    with pytest.raises(RuntimeError):
        with metrics.timer("failure.duration"):
            raise RuntimeError("boom")
    assert metrics.snapshot().find("failure.duration").value == 1.0  # type: ignore[union-attr]


def test_counter_updates_are_thread_safe() -> None:
    metrics = MetricsRegistry()
    with ThreadPoolExecutor(max_workers=8) as executor:
        tuple(executor.map(lambda _: metrics.increment("work"), range(1000)))
    assert metrics.snapshot().find("work").value == 1000.0  # type: ignore[union-attr]


def test_snapshot_is_deterministically_sorted() -> None:
    metrics = MetricsRegistry()
    metrics.increment("zeta")
    metrics.increment("alpha")
    assert [sample.key.name for sample in metrics.snapshot().samples] == ["alpha", "zeta"]


def test_clear_removes_every_metric_kind() -> None:
    metrics = MetricsRegistry()
    metrics.increment("counter")
    metrics.set_gauge("gauge", 1)
    metrics.observe("distribution", 1)
    metrics.clear()
    assert metrics.snapshot().samples == ()


def test_histogram_records_cumulative_buckets() -> None:
    metrics = MetricsRegistry()
    metrics.observe_histogram("latency", 0.1, buckets=(0.5, 1.0))
    metrics.observe_histogram("latency", 0.7, buckets=(0.5, 1.0))
    sample = metrics.snapshot().find("latency")
    assert sample is not None
    assert sample.kind is MetricKind.HISTOGRAM
    assert sample.buckets == ((0.5, 1), (1.0, 2))
    assert sample.count == 2


def test_histogram_rejects_changed_boundaries() -> None:
    metrics = MetricsRegistry()
    metrics.observe_histogram("latency", 0.1, buckets=(0.5,))
    with pytest.raises(ValueError):
        metrics.observe_histogram("latency", 0.2, buckets=(1.0,))


def test_noop_metrics_retains_no_state() -> None:
    metrics = NoOpMetricsRegistry()
    metrics.increment("requests")
    metrics.set_gauge("depth", 2)
    metrics.observe("size", 4)
    metrics.observe_histogram("latency", 0.1)
    with metrics.timer("duration"):
        pass
    assert metrics.snapshot().samples == ()
