import asyncio
import logging
from typing import Dict, Any, Callable, Optional
from src.telemetry.context import TraceContext
from src.resilience.retry import RetryPolicy, dlq_instance

logger = logging.getLogger("sarathi.worker")

class ResilientWorkerEngine:
    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.metrics = {"processed": 0, "failed": 0, "retried": 0, "dlq_routed": 0}
        self._is_shutting_down = False

    async def process_task(
        self,
        task_id: str,
        handler: Callable[..., Any],
        payload: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> Any:
        if self._is_shutting_down:
            raise RuntimeError("Worker engine is shutting down. Task rejected.")

        if trace_id:
            TraceContext.set_context(trace_id=trace_id)
        else:
            TraceContext.get_trace_id()

        try:
            result = await self.retry_policy.execute(handler, task_id, payload, payload)
            self.metrics["processed"] += 1
            return result
        except Exception as e:
            self.metrics["failed"] += 1
            self.metrics["dlq_routed"] = dlq_instance.size()
            raise e

    async def shutdown(self) -> None:
        self._is_shutting_down = True
