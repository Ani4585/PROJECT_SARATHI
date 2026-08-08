import threading
from typing import Dict, List, Optional, Any

class Counter:
    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.value = 0.0
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0):
        if value < 0:
            raise ValueError("Counter cannot be decremented")
        with self._lock:
            self.value += value

class Gauge:
    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.value = 0.0
        self._lock = threading.Lock()

    def set(self, value: float):
        with self._lock:
            self.value = float(value)

    def inc(self, value: float = 1.0):
        with self._lock:
            self.value += value

    def dec(self, value: float = 1.0):
        with self._lock:
            self.value -= value

class Histogram:
    def __init__(self, name: str, description: str = "", buckets: Optional[List[float]] = None):
        self.name = name
        self.description = description
        self.buckets = sorted(buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        self.bucket_counts = {b: 0 for b in self.buckets}
        self.sum = 0.0
        self.count = 0
        self._lock = threading.Lock()

    def observe(self, value: float):
        with self._lock:
            self.sum += value
            self.count += 1
            for b in self.buckets:
                if value <= b:
                    self.bucket_counts[b] += 1

class PrometheusExporter:
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}

    def register_counter(self, counter: Counter):
        self.counters[counter.name] = counter

    def register_gauge(self, gauge: Gauge):
        self.gauges[gauge.name] = gauge

    def register_histogram(self, histogram: Histogram):
        self.histograms[histogram.name] = histogram

    def export(self) -> str:
        lines = []
        for name, c in self.counters.items():
            lines.append(f"# HELP {name} {c.description}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {c.value}")

        for name, g in self.gauges.items():
            lines.append(f"# HELP {name} {g.description}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {g.value}")

        for name, h in self.histograms.items():
            lines.append(f"# HELP {name} {h.description}")
            lines.append(f"# TYPE {name} histogram")
            for b, count in h.bucket_counts.items():
                lines.append(f'{name}_bucket{{le="{b}"}} {count}')
            lines.append(f'{name}_bucket{{le="+Inf"}} {h.count}')
            lines.append(f"{name}_sum {h.sum}")
            lines.append(f"{name}_count {h.count}")

        return "\n".join(lines)
