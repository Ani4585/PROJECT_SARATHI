from typing import Optional
from .models import PlatformConfig, PlatformHealthReport

class SarathiPlatform:
    def __init__(self, config: Optional[PlatformConfig] = None):
        self.config = config or PlatformConfig()
        self.is_started = False
        self.is_stopped = False

    async def start(self):
        self.is_started = True
        self.is_stopped = False

    async def stop(self):
        self.is_stopped = True
        self.is_started = False

    def get_health_report(self) -> PlatformHealthReport:
        report = PlatformHealthReport()
        subsystems = [
            "async_runtime", "background_tasks", "scheduler",
            "resilience", "caching", "telemetry", "security",
            "gateway", "hardening", "sdk", "cloud", "multitenancy", "cqrs"
        ]
        for sub in subsystems:
            report.add_status(sub, "UP" if self.is_started else "DOWN")
        return report
