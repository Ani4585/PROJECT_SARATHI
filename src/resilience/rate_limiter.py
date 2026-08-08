import time
from typing import Any, Dict, Optional

class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.last_refill = time.time()

    def _refill(self) -> None:
        now = time.time()
        delta = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + delta * self.refill_rate)
        self.last_refill = now

    async def acquire(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
