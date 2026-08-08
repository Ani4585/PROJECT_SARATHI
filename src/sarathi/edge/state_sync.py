import time
from typing import Dict, Any
from .models import VectorClock, SyncDelta

class DistributedStateSync:
    def __init__(self, node_id: str, policy: str = "LAST_WRITE_WINS"):
        self.node_id = node_id
        self.policy = policy
        self.state: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.clock = VectorClock()

    def set(self, key: str, value: Any):
        self.clock.increment(self.node_id)
        self.state[key] = value
        self.timestamps[key] = time.time()

    def sync_delta(self, key: str, value: Any, remote_ts: float, remote_clock: VectorClock):
        self.clock.merge(remote_clock)
        if key not in self.state:
            self.state[key] = value
            self.timestamps[key] = remote_ts
        else:
            if self.policy == "LAST_WRITE_WINS":
                if remote_ts > self.timestamps[key]:
                    self.state[key] = value
                    self.timestamps[key] = remote_ts
