from dataclasses import dataclass, field
from typing import Dict, Set, Any

@dataclass
class VectorClock:
    clock: Dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str):
        self.clock[node_id] = self.clock.get(node_id, 0) + 1

    def merge(self, other: 'VectorClock'):
        for node_id, count in other.clock.items():
            self.clock[node_id] = max(self.clock.get(node_id, 0), count)

    def is_concurrent(self, other: 'VectorClock') -> bool:
        greater = False
        smaller = False
        all_nodes = set(self.clock.keys()).union(set(other.clock.keys()))
        for n in all_nodes:
            v1 = self.clock.get(n, 0)
            v2 = other.clock.get(n, 0)
            if v1 > v2:
                greater = True
            elif v1 < v2:
                smaller = True
        return greater and smaller

@dataclass
class SyncDelta:
    key: str
    value: Any
    timestamp: float
    vector_clock: VectorClock
