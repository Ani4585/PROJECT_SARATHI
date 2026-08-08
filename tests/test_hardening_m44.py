import asyncio
import time
import pytest
from sarathi.hardening import (
    HardeningResult,
    HardeningReport,
    HardeningAuditor,
    default_async_runtime_check,
    default_security_check,
    ShutdownManager,
    ProductionBenchmarkSuite,
)

def test_hardening_auditor_execution():
    auditor = HardeningAuditor()
    auditor.register_check(default_async_runtime_check)
    auditor.register_check(default_security_check)

    report = auditor.run_audit()
    assert report.total_checks == 2
    assert report.passed_checks == 2
    assert report.is_production_ready is True

def test_shutdown_manager_graceful_drain():
    async def _test():
        sm = ShutdownManager(drain_timeout=0.1)

        async def worker_task():
            await asyncio.sleep(0.01)
            return "ok"

        t = asyncio.create_task(worker_task())
        sm.track_task(t)

        await sm.initiate_graceful_shutdown()
        assert sm.is_shutting_down is True
        assert len(sm.active_tasks) == 0

    asyncio.run(_test())

def test_production_benchmark_suite():
    stats = ProductionBenchmarkSuite.measure_latency(lambda: time.sleep(0.0001), iterations=20)
    assert "p50_ms" in stats
    assert "p95_ms" in stats
    assert stats["p50_ms"] >= 0.0
