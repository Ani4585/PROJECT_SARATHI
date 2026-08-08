import time
from typing import Tuple

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate)
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> Tuple[bool, int, float]:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        if self.tokens >= tokens:
            self.tokens -= tokens
            remaining = int(self.tokens)
            reset_after = (self.capacity - self.tokens) / self.refill_rate if self.refill_rate > 0 else 0.0
            return True, remaining, max(0.0, reset_after)
        else:
            needed = tokens - self.tokens
            retry_after = needed / self.refill_rate if self.refill_rate > 0 else 0.0
            reset_after = (self.capacity - self.tokens) / self.refill_rate if self.refill_rate > 0 else 0.0
            return False, int(self.tokens), max(0.0, retry_after)

class SlidingWindowCounter:
    def __init__(self, limit: int, window_seconds: float):
        self.limit = limit
        self.window_seconds = window_seconds
        self.timestamps = []

    def consume(self, tokens: int = 1) -> Tuple[bool, int, float]:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        self.timestamps = [t for t in self.timestamps if t > cutoff]

        if len(self.timestamps) + tokens <= self.limit:
            for _ in range(tokens):
                self.timestamps.append(now)
            remaining = self.limit - len(self.timestamps)
            reset_after = self.window_seconds - (now - self.timestamps[0]) if self.timestamps else 0.0
            return True, remaining, max(0.0, reset_after)
        else:
            oldest = self.timestamps[0] if self.timestamps else now
            retry_after = max(0.0, self.window_seconds - (now - oldest))
            remaining = max(0, self.limit - len(self.timestamps))
            return False, remaining, max(0.0, retry_after)

class LeakyBucket:
    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = float(capacity)
        self.leak_rate = float(leak_rate)
        self.water = 0.0
        self.last_leak = time.monotonic()

    def consume(self, tokens: int = 1) -> Tuple[bool, int, float]:
        now = time.monotonic()
        elapsed = now - self.last_leak
        self.last_leak = now
        self.water = max(0.0, self.water - elapsed * self.leak_rate)

        if self.water + tokens <= self.capacity:
            self.water += tokens
            remaining = int(self.capacity - self.water)
            reset_after = self.water / self.leak_rate if self.leak_rate > 0 else 0.0
            return True, remaining, max(0.0, reset_after)
        else:
            overflow = (self.water + tokens) - self.capacity
            retry_after = overflow / self.leak_rate if self.leak_rate > 0 else 0.0
            remaining = int(self.capacity - self.water)
            return False, remaining, max(0.0, retry_after)
