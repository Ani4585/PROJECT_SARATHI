import asyncio
import logging
import random
import time
from typing import Callable, Any, Dict, Optional, List, Type
from src.telemetry.context import TraceContext

logger = logging.getLogger("sarathi.resilience")

class DeadLetterQueue:
    def __init__(self) -> None:
        self._dlq_store: List[Dict[str, Any]] = []

    def push(self, task_id: str, payload: Dict[str, Any], exception: Exception, trace_info: Dict[str, str]) -> None:
        entry = {
            "task_id": task_id,
            "payload": payload,
            "error": str(exception),
            "error_type": type(exception).__name__,
            "failed_at": time.time(),
            "trace_context": trace_info
        }
        self._dlq_store.append(entry)

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        return list(self._dlq_store)

    def size(self) -> int:
        return len(self._dlq_store)

dlq_instance = DeadLetterQueue()

class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay_sec: float = 0.1,
        max_delay_sec: float = 2.0,
        backoff_factor: float = 2.0,
        retryable_exceptions: Optional[List[Type[BaseException]]] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay_sec
        self.max_delay = max_delay_sec
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = tuple(retryable_exceptions or [Exception])

    def calculate_delay(self, attempt: int) -> float:
        calculated = self.base_delay * (self.backoff_factor ** attempt)
        return random.uniform(0, min(self.max_delay, calculated))

    async def execute(
        self,
        func: Callable[..., Any],
        task_id: str,
        payload: Dict[str, Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        attempt = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except self.retryable_exceptions as exc:
                attempt += 1
                if attempt > self.max_retries:
                    dlq_instance.push(task_id, payload, exc, TraceContext.export_context())
                    raise exc
                delay = self.calculate_delay(attempt)
                await asyncio.sleep(delay)
