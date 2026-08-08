import asyncio
import sarathi
import pytest
from sarathi.resilience import CircuitBreaker, CircuitState
from sarathi.ratelimit import InMemoryRateLimiter
from sarathi.caching import TwoLevelCache
from sarathi.telemetry import Counter, PrometheusExporter, Tracer, SpanContext
from sarathi.security import UserIdentity, JWTManager, SecurityContext, require_role
from sarathi.gateway import GatewayRouter, GatewayRequest, CORSInterceptor, OpenAPIGenerator
from sarathi.hardening import HardeningAuditor, ShutdownManager, ProductionBenchmarkSuite

def test_version_metadata():
    assert sarathi.__version__ == "0.9.0-rc1"

def test_master_resilience_and_caching_integration():
    cb = CircuitBreaker(failure_threshold=2)
    assert cb.state == CircuitState.CLOSED

    limiter = InMemoryRateLimiter(limit=5, period=1.0)
    r = limiter.acquire("key1")
    assert r.allowed is True

    cache = TwoLevelCache()
    assert cache.metrics["l1_hits"] == 0

def test_master_telemetry_integration():
    c = Counter("master_requests", "Total master requests")
    c.inc(1)
    exporter = PrometheusExporter()
    exporter.register_counter(c)
    out = exporter.export()
    assert "master_requests 1.0" in out

    ctx = SpanContext(trace_id="4bf92f3577b34da6a3ce929d0e0e4736", span_id="00f067aa0ba902b7")
    assert "4bf92f3577b34da6a3ce929d0e0e4736" in ctx.to_traceparent()

def test_master_security_integration():
    jwt_mgr = JWTManager(secret_key="master_secret")
    token = jwt_mgr.encode({"sub": "admin_user", "roles": ["admin"]})
    decoded = jwt_mgr.decode(token)
    assert decoded["sub"] == "admin_user"

    user = UserIdentity(user_id="admin_user", username="admin", roles={"admin"})
    t = SecurityContext.set_current_user(user)
    try:
        @require_role("admin")
        def admin_only():
            return "ok"
        assert admin_only() == "ok"
    finally:
        SecurityContext.reset(t)

def test_master_gateway_integration():
    async def _test():
        router = GatewayRouter()
        router.add_interceptor(CORSInterceptor())
        router.add_route("/api/v1/health", ["GET"], lambda ctx: ctx.response.json({"status": "UP"}))

        req = GatewayRequest(method="GET", path="/api/v1/health")
        res = await router.dispatch(req)
        assert res.status_code == 200
        assert "UP" in res.body

        gen = OpenAPIGenerator()
        spec = gen.generate(router)
        assert spec["openapi"] == "3.1.0"

    asyncio.run(_test())

def test_master_hardening_integration():
    async def _test():
        auditor = HardeningAuditor()
        report = auditor.run_audit()
        assert report.is_production_ready is True

        sm = ShutdownManager(drain_timeout=0.1)
        await sm.initiate_graceful_shutdown()
        assert sm.is_shutting_down is True

        stats = ProductionBenchmarkSuite.measure_latency(lambda: None, iterations=10)
        assert "p50_ms" in stats

    asyncio.run(_test())
