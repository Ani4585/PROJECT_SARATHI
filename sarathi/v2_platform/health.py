"""Health Probe & Metrics."""
class SystemHealthProbe:
    def __init__(self, platform): self.platform = platform
    def check_liveness(self): return self.platform.is_booted
    def check_readiness(self): return self.platform.is_booted and self.platform.get_health_status()["status"] == "HEALTHY"

class PlatformMetricsReporter:
    def __init__(self): self.execution_times = []
    def record_execution(self, duration_ms: float): self.execution_times.append(duration_ms)
    def get_summary(self):
        n = len(self.execution_times)
        return {"total_executions": n, "min_duration_ms": min(self.execution_times) if n else 0, "max_duration_ms": max(self.execution_times) if n else 0, "avg_duration_ms": sum(self.execution_times)/n if n else 0}
