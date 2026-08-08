import os
from pathlib import Path

def write_file(path_str: str, content: str):
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"[UPDATED] {path_str}")

SARATHI_INIT = '''
try:
    from scripts.tooling.cli.application import create_cli_application, main
except ImportError:
    try:
        from src.cli.application import create_cli_application, main
    except ImportError:
        pass

from . import caching, ratelimit, resilience, telemetry

__all__ = [
    "create_cli_application",
    "main",
    "caching",
    "ratelimit",
    "resilience",
    "telemetry",
]
'''

write_file("sarathi/__init__.py", SARATHI_INIT)
write_file("src/sarathi/__init__.py", SARATHI_INIT)

TEST_M40_SYNC = '''
import asyncio
import time
import pytest
from sarathi.resilience import (
    CircuitState,
    CircuitBreakerOpenException,
    CircuitBreakerConfig,
    CircuitBreaker,
    circuit_breaker,
    BackoffStrategy,
    RetryPolicy,
    retry,
    BulkheadFullException,
    Bulkhead,
    bulkhead,
    fallback,
)
from sarathi.ratelimit import (
    RateLimitResult,
    RateLimitExceededException,
    TokenBucket,
    SlidingWindowCounter,
    LeakyBucket,
    InMemoryRateLimiter,
    DistributedRateLimiter,
    rate_limit,
)
from sarathi.caching import TwoLevelCache, DistributedCache, DistributedCacheConfig

def test_circuit_breaker_state_transitions():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, success_threshold=2)
    assert cb.state == CircuitState.CLOSED

    def fail():
        raise ValueError("failing function")

    def success():
        return "ok"

    with pytest.raises(ValueError):
        cb.call_sync(fail)
    assert cb.state == CircuitState.CLOSED

    with pytest.raises(ValueError):
        cb.call_sync(fail)
    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException) as exc_info:
        cb.call_sync(success)
    assert "OPEN" in str(exc_info.value)

    time.sleep(0.12)
    assert cb.state == CircuitState.HALF_OPEN

    assert cb.call_sync(success) == "ok"
    assert cb.state == CircuitState.HALF_OPEN

    assert cb.call_sync(success) == "ok"
    assert cb.state == CircuitState.CLOSED

def test_async_circuit_breaker_decorator():
    async def _test():
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)

        @circuit_breaker(cb)
        async def fetch_remote(should_fail=False):
            if should_fail:
                raise KeyError("remote failure")
            return "data"

        assert await fetch_remote(False) == "data"

        with pytest.raises(KeyError):
            await fetch_remote(True)

        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitBreakerOpenException):
            await fetch_remote(False)

    asyncio.run(_test())

def test_retry_policy_fixed_backoff():
    attempts = 0
    def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("flaky connection")
        return "recovered"

    policy = RetryPolicy(max_retries=3, initial_delay=0.001, strategy=BackoffStrategy.FIXED)
    result = policy.execute(flaky)
    assert result == "recovered"
    assert attempts == 3

def test_retry_policy_async_decorator():
    async def _test():
        retries = 0
        policy = RetryPolicy(max_retries=2, initial_delay=0.001, strategy=BackoffStrategy.EXPONENTIAL)

        @retry(policy)
        async def async_job():
            nonlocal retries
            retries += 1
            if retries < 2:
                raise ValueError("async attempt fail")
            return "job_done"

        res = await async_job()
        assert res == "job_done"
        assert retries == 2

    asyncio.run(_test())

def test_bulkhead_capacity_exhaustion():
    async def _test():
        bh = Bulkhead(max_concurrent=1, max_queued=1, name="test_bulkhead")

        async def long_task():
            await asyncio.sleep(0.05)
            return "completed"

        t1 = asyncio.create_task(bh.execute_async(long_task))
        await asyncio.sleep(0.005)
        t2 = asyncio.create_task(bh.execute_async(long_task))
        await asyncio.sleep(0.005)

        with pytest.raises(BulkheadFullException) as exc_info:
            await bh.execute_async(long_task)
        assert "test_bulkhead" in str(exc_info.value)

        res1, res2 = await asyncio.gather(t1, t2)
        assert res1 == "completed" and res2 == "completed"

    asyncio.run(_test())

def test_fallback_mechanism():
    async def _test():
        @fallback("static_fallback")
        def sync_fail():
            raise RuntimeError("sync fail")

        @fallback(lambda exc: f"handled_{exc.__class__.__name__}")
        async def async_fail():
            raise KeyError("async key error")

        assert sync_fail() == "static_fallback"
        assert await async_fail() == "handled_KeyError"

    asyncio.run(_test())

def test_rate_limiter_token_bucket():
    limiter = InMemoryRateLimiter(limit=2, period=1.0, algorithm="token_bucket")

    r1 = limiter.acquire("client1")
    assert r1.allowed is True
    assert r1.remaining == 1

    r2 = limiter.acquire("client1")
    assert r2.allowed is True
    assert r2.remaining == 0

    r3 = limiter.acquire("client1")
    assert r3.allowed is False
    assert r3.retry_after > 0.0

def test_rate_limit_decorator_dynamic_key():
    async def _test():
        limiter = InMemoryRateLimiter(limit=1, period=1.0)

        @rate_limit(limiter, key_func=lambda req: f"ip:{req['ip']}")
        async def process_request(req):
            return f"response_{req['ip']}"

        req_a = {"ip": "10.0.0.1"}
        req_b = {"ip": "10.0.0.2"}

        assert await process_request(req_a) == "response_10.0.0.1"
        
        with pytest.raises(RateLimitExceededException):
            await process_request(req_a)

        assert await process_request(req_b) == "response_10.0.0.2"

    asyncio.run(_test())

def test_two_level_cache_stampede_protection():
    async def _test():
        class MockL2Store:
            def __init__(self):
                self.store = {}
            async def get(self, k):
                return self.store.get(k)
            async def set(self, k, v, ttl=None):
                self.store[k] = v
            async def delete(self, k):
                self.store.pop(k, None)

        l2 = MockL2Store()
        cache = TwoLevelCache(l2_backend=l2, l1_ttl=10.0, l2_ttl=100.0)

        loader_calls = 0
        def expensive_loader():
            nonlocal loader_calls
            loader_calls += 1
            return "expensive_data"

        results = await asyncio.gather(
            cache.get_or_load("key1", expensive_loader),
            cache.get_or_load("key1", expensive_loader),
            cache.get_or_load("key1", expensive_loader)
        )

        assert results == ["expensive_data", "expensive_data", "expensive_data"]
        assert loader_calls == 1

    asyncio.run(_test())

def test_two_level_cache_l2_failure_bypass():
    async def _test():
        class FailingL2Store:
            async def get(self, k):
                raise ConnectionError("Redis connection refused")
            async def set(self, k, v, ttl=None):
                raise ConnectionError("Redis connection refused")

        cache = TwoLevelCache(l2_backend=FailingL2Store(), bypass_on_l2_error=True)

        res = await cache.get_or_load("key2", lambda: "fallback_value")
        assert res == "fallback_value"
        assert cache.metrics["l2_errors"] > 0

    asyncio.run(_test())
'''

write_file("tests/test_resilience_m40.py", TEST_M40_SYNC)

TEST_M41_SYNC = '''
import asyncio
import pytest
from sarathi.telemetry import (
    Counter,
    Gauge,
    Histogram,
    PrometheusExporter,
    SpanContext,
    Span,
    Tracer,
    trace,
)

def test_counter_inc():
    c = Counter("test_counter", "Test Description")
    c.inc(5)
    assert c.value == 5.0
    with pytest.raises(ValueError):
        c.inc(-1)

def test_gauge_set_inc_dec():
    g = Gauge("test_gauge", "Gauge Description")
    g.set(10)
    assert g.value == 10.0
    g.inc(2)
    assert g.value == 12.0
    g.dec(4)
    assert g.value == 8.0

def test_prometheus_exporter_output():
    exporter = PrometheusExporter()
    c = Counter("http_requests_total", "Total Requests")
    c.inc(10)
    exporter.register_counter(c)

    g = Gauge("active_tasks", "Active Background Tasks")
    g.set(3)
    exporter.register_gauge(g)

    output = exporter.export()
    assert "# TYPE http_requests_total counter" in output
    assert "http_requests_total 10.0" in output
    assert "active_tasks 3.0" in output

def test_w3c_traceparent_parsing():
    ctx = SpanContext(trace_id="4bf92f3577b34da6a3ce929d0e0e4736", span_id="00f067aa0ba902b7")
    header = ctx.to_traceparent()
    assert header == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

    parsed = SpanContext.from_traceparent(header)
    assert parsed is not None
    assert parsed.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed.span_id == "00f067aa0ba902b7"

def test_parent_child_span_linkage():
    tracer = Tracer("test_service")
    with tracer.start_span("root") as root:
        root.set_attribute("env", "prod")
        with tracer.start_span("child") as child:
            child.set_attribute("db", "postgres")

    assert len(tracer.finished_spans) == 2
    child_span = tracer.finished_spans[0]
    root_span = tracer.finished_spans[1]

    assert child_span.context.trace_id == root_span.context.trace_id
    assert child_span.parent_span_id == root_span.context.span_id

def test_trace_decorator_async():
    async def _test():
        tracer = Tracer("async_service")

        @trace(tracer, "async_operation")
        async def fetch_data():
            await asyncio.sleep(0.01)
            return "data"

        res = await fetch_data()
        assert res == "data"
        assert len(tracer.finished_spans) == 1
        assert tracer.finished_spans[0].name == "async_operation"

    asyncio.run(_test())
'''

write_file("tests/test_telemetry_m41.py", TEST_M41_SYNC)
print("All fix updates completed!")
