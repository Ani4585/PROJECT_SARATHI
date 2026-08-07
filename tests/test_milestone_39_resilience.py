import pytest
import asyncio
from src.telemetry.context import TraceContext
from src.resilience.retry import RetryPolicy, dlq_instance
from src.async_runtime.resilient_worker import ResilientWorkerEngine

def test_trace_context_propagation():
    async def _test():
        TraceContext.reset()
        t_id = "test-trace-12345"
        TraceContext.set_context(trace_id=t_id)
        ctx = TraceContext.export_context()
        assert ctx["trace_id"] == t_id
        assert ctx["span_id"].startswith("sp-")
    asyncio.run(_test())

def test_retry_policy_success_after_retry():
    async def _test():
        calls = 0
        async def flaky_func(payload):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("Temporary failure")
            return "success"

        policy = RetryPolicy(max_retries=3, base_delay_sec=0.01)
        worker = ResilientWorkerEngine(retry_policy=policy)
        
        res = await worker.process_task("task-101", flaky_func, {"key": "val"})
        assert res == "success"
        assert calls == 3
        assert worker.metrics["processed"] == 1
    asyncio.run(_test())

def test_retry_policy_dlq_fallback():
    async def _test():
        async def failing_func(payload):
            raise KeyError("Unrecoverable error")

        policy = RetryPolicy(max_retries=2, base_delay_sec=0.01)
        worker = ResilientWorkerEngine(retry_policy=policy)

        initial_dlq_size = dlq_instance.size()
        with pytest.raises(KeyError):
            await worker.process_task("task-102", failing_func, {"key": "val"})

        assert dlq_instance.size() == initial_dlq_size + 1
        failed_item = dlq_instance.get_failed_tasks()[-1]
        assert failed_item["task_id"] == "task-102"
        assert failed_item["error_type"] == "KeyError"
    asyncio.run(_test())

def test_worker_graceful_shutdown():
    async def _test():
        worker = ResilientWorkerEngine()
        await worker.shutdown()
        
        async def dummy_func(payload):
            return True

        with pytest.raises(RuntimeError, match="Worker engine is shutting down"):
            await worker.process_task("task-103", dummy_func, {})
    asyncio.run(_test())
