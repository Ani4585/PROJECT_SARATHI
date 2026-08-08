from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class HardeningResult:
    check_name: str
    status: str  # "PASS", "WARN", "FAIL"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HardeningReport:
    total_checks: int
    passed_checks: int
    warn_checks: int
    failed_checks: int
    results: List[HardeningResult] = field(default_factory=list)

    @property
    def is_production_ready(self) -> bool:
        return self.failed_checks == 0
