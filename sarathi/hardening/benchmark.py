import time
from typing import Callable, Dict

class ProductionBenchmarkSuite:
    @staticmethod
    def measure_latency(fn: Callable, iterations: int = 50) -> Dict[str, float]:
        latencies = []
        for _ in range(iterations):
            start = time.monotonic()
            fn()
            latencies.append((time.monotonic() - start) * 1000.0) # ms
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        avg = sum(latencies) / len(latencies)
        return {"p50_ms": p50, "p95_ms": p95, "avg_ms": avg}
