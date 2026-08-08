import asyncio
import functools
import inspect
import time
from enum import Enum
from typing import Callable, Optional, Tuple, Type, Any, Dict

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerOpenException(Exception):
    """Raised when call is attempted while Circuit Breaker is OPEN."""
    def __init__(self, message: str = "Circuit breaker is OPEN", retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after

class CircuitBreakerConfig:
    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
        success_threshold: int = 2,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exceptions = expected_exceptions

class CircuitBreaker:
    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
        success_threshold: int = 2,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        config: Optional[CircuitBreakerConfig] = None
    ):
        if config:
            self.name = config.name
            self.failure_threshold = config.failure_threshold
            self.recovery_timeout = config.recovery_timeout
            self.success_threshold = config.success_threshold
            self.expected_exceptions = config.expected_exceptions
        else:
            self.name = name
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.success_threshold = success_threshold
            self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_state_change = time.monotonic()
        self._last_failure_time = 0.0
        self._async_lock: Optional[asyncio.Lock] = None

        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0,
            "state_transitions": 0
        }

    @property
    def async_lock(self) -> asyncio.Lock:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock

    @property
    def state(self) -> CircuitState:
        self._check_state_transition()
        return self._state

    def _check_state_transition(self):
        if self._state == CircuitState.OPEN:
            now = time.monotonic()
            if now - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                self._last_state_change = now
                self.metrics["state_transitions"] += 1

    def record_success(self):
        self.metrics["total_calls"] += 1
        self.metrics["successful_calls"] += 1
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._last_state_change = time.monotonic()
                self.metrics["state_transitions"] += 1
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def record_failure(self, exc: Exception):
        if isinstance(exc, self.expected_exceptions):
            self.metrics["total_calls"] += 1
            self.metrics["failed_calls"] += 1
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == CircuitState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                if self._state != CircuitState.OPEN:
                    self._state = CircuitState.OPEN
                    self._last_state_change = self._last_failure_time
                    self.metrics["state_transitions"] += 1

    def call_sync(self, func: Callable, *args, **kwargs):
        self._check_state_transition()
        if self._state == CircuitState.OPEN:
            self.metrics["rejected_calls"] += 1
            retry_after = max(0.0, self.recovery_timeout - (time.monotonic() - self._last_failure_time))
            raise CircuitBreakerOpenException(f"Circuit '{self.name}' is OPEN", retry_after=retry_after)

        try:
            res = func(*args, **kwargs)
            self.record_success()
            return res
        except Exception as e:
            if isinstance(e, self.expected_exceptions):
                self.record_failure(e)
            raise

    async def call_async(self, func: Callable, *args, **kwargs):
        async with self.async_lock:
            self._check_state_transition()
            if self._state == CircuitState.OPEN:
                self.metrics["rejected_calls"] += 1
                retry_after = max(0.0, self.recovery_timeout - (time.monotonic() - self._last_failure_time))
                raise CircuitBreakerOpenException(f"Circuit '{self.name}' is OPEN", retry_after=retry_after)

        try:
            res = func(*args, **kwargs)
            if inspect.iscoroutine(res) or asyncio.iscoroutinefunction(func):
                res = await res
            async with self.async_lock:
                self.record_success()
            return res
        except Exception as e:
            async with self.async_lock:
                if isinstance(e, self.expected_exceptions):
                    self.record_failure(e)
            raise

    def __call__(self, func: Callable):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.call_async(func, *args, **kwargs)
            return wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self.call_sync(func, *args, **kwargs)
            return wrapper

def circuit_breaker(cb_or_name: Any = "default", **cb_kwargs):
    if isinstance(cb_or_name, CircuitBreaker):
        cb = cb_or_name
    elif callable(cb_or_name) and not isinstance(cb_or_name, str):
        cb = CircuitBreaker()
        return cb(cb_or_name)
    else:
        cb = CircuitBreaker(name=str(cb_or_name), **cb_kwargs)

    def decorator(fn):
        return cb(fn)
    return decorator
