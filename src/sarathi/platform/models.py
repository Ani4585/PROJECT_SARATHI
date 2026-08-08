from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class PlatformConfig:
    app_name: str = "SarathiPlatformApp"
    version: str = "1.5.0"
    environment: str = "production"

@dataclass
class SubsystemStatus:
    name: str
    status: str  # "UP", "DEGRADED", "DOWN"
    details: Dict[str, Any] = field(default_factory=dict)

class PlatformHealthReport:
    def __init__(self):
        self.subsystems: List[SubsystemStatus] = []

    def add_status(self, name: str, status: str, details: Optional[Dict[str, Any]] = None):
        self.subsystems.append(SubsystemStatus(name=name, status=status, details=details or {}))

    @property
    def is_healthy(self) -> bool:
        return all(s.status == "UP" for s in self.subsystems)
