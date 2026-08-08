from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ProbeResult:
    status: str  # "UP", "DOWN"
    status_code: int
    details: Dict[str, Any] = field(default_factory=dict)

class K8sProbeHandler:
    def __init__(self):
        self.is_live = True
        self.is_ready = True

    def liveness_probe(self) -> ProbeResult:
        if self.is_live:
            return ProbeResult(status="UP", status_code=200, details={"alive": True})
        return ProbeResult(status="DOWN", status_code=500, details={"alive": False})

    def readiness_probe(self) -> ProbeResult:
        if self.is_ready:
            return ProbeResult(status="UP", status_code=200, details={"ready": True})
        return ProbeResult(status="DOWN", status_code=503, details={"ready": False})
