"""
AI Circuit Breaker for Agent Tools and LLM Drivers.
"""
import time
from enum import Enum
from typing import Callable, Awaitable, Any, Optional

class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Tripped, blocking requests
    HALF_OPEN = "HALF_OPEN"# Testing recovery

class AICircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 2.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    async def call(self, func: Callable[[], Awaitable[Any]]) -> Any:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_state_change >= self.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
            else:
                raise RuntimeError("Circuit breaker is OPEN. Call blocked.")

        try:
            result = await func()
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = now
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.last_state_change = now
            raise e
