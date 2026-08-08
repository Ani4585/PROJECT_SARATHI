import asyncio
import functools
import inspect
import random
import time
from enum import Enum
from typing import Callable, Optional, Tuple, Type, Any

class BackoffStrategy(str, Enum):
    FIXED = "FIXED"
    EXPONENTIAL = "EXPONENTIAL"
    EXPONENTIAL_JITTER = "EXPONENTIAL_JITTER"

class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 0.1,
        max_delay: float = 5.0,
        backoff_factor: float = 2.0,
        strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
        retry_on: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable[[int, Exception, float], None]] = None
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.strategy = strategy
        self.retry_on = retry_on
        self.on_retry = on_retry
        
        self.metrics = {
            "attempts": 0,
            "retries": 0,
            "successes": 0,
            "failures": 0
        }

    def calculate_delay(self, attempt: int) -> float:
        if self.strategy == BackoffStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        elif self.strategy == BackoffStrategy.EXPONENTIAL_JITTER:
            base_delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
            delay = base_delay * (0.5 + random.random() * 0.5)
        else:
            delay = self.initial_delay
        return min(delay, self.max_delay)

    def execute(self, func: Callable, *args, **kwargs):
        attempt = 0
        while True:
            attempt += 1
            self.metrics["attempts"] += 1
            try:
                res = func(*args, **kwargs)
                self.metrics["successes"] += 1
                return res
            except self.retry_on as exc:
                if attempt > self.max_retries:
                    self.metrics["failures"] += 1
                    raise exc
                self.metrics["retries"] += 1
                delay = self.calculate_delay(attempt)
                if self.on_retry:
                    self.on_retry(attempt, exc, delay)
                time.sleep(delay)

    async def execute_async(self, func: Callable, *args, **kwargs):
        attempt = 0
        while True:
            attempt += 1
            self.metrics["attempts"] += 1
            try:
                res = func(*args, **kwargs)
                if inspect.iscoroutine(res) or asyncio.iscoroutinefunction(func):
                    res = await res
                self.metrics["successes"] += 1
                return res
            except self.retry_on as exc:
                if attempt > self.max_retries:
                    self.metrics["failures"] += 1
                    raise exc
                self.metrics["retries"] += 1
                delay = self.calculate_delay(attempt)
                if self.on_retry:
                    self.on_retry(attempt, exc, delay)
                await asyncio.sleep(delay)

    def __call__(self, func: Callable):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute_async(func, *args, **kwargs)
            return wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute(func, *args, **kwargs)
            return wrapper

def retry(policy_or_func: Any = None, **retry_kwargs):
    if isinstance(policy_or_func, RetryPolicy):
        policy = policy_or_func
    elif callable(policy_or_func):
        policy = RetryPolicy(**retry_kwargs)
        return policy(policy_or_func)
    else:
        policy = RetryPolicy(**retry_kwargs)

    def decorator(fn):
        return policy(fn)
    return decorator
