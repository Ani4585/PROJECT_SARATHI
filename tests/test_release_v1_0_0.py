import asyncio
import sarathi
import pytest
from sarathi.hardening import HardeningAuditor, ShutdownManager, ProductionBenchmarkSuite
from sarathi.gateway import GatewayRouter, GatewayRequest, CORSInterceptor, OpenAPIGenerator
from sarathi.security import UserIdentity, JWTManager, require_role, SecurityContext
from sarathi.telemetry import Counter, PrometheusExporter, Tracer
from sarathi.caching import TwoLevelCache
from sarathi.resilience import CircuitBreaker, CircuitState

def test_v100_ga_version_string():
    assert sarathi.__version__ == "1.0.0"

def test_v100_subsystem_exports():
    assert hasattr(sarathi, "caching")
    assert hasattr(sarathi, "ratelimit")
    assert hasattr(sarathi, "resilience")
    assert hasattr(sarathi, "telemetry")
    assert hasattr(sarathi, "security")
    assert hasattr(sarathi, "gateway")
    assert hasattr(sarathi, "hardening")

def test_v100_security_jwt_and_rbac():
    jwt_mgr = JWTManager(secret_key="v100_ga_secret")
    token = jwt_mgr.encode({"sub": "admin_user", "roles": ["admin"]})
    decoded = jwt_mgr.decode(token)
    assert decoded["sub"] == "admin_user"

    user = UserIdentity(user_id="u1", username="admin_user", roles={"admin"})
    tok = SecurityContext.set_current_user(user)
    try:
        @require_role("admin")
        def admin_action():
            return "ok_v100"
        assert admin_action() == "ok_v100"
    finally:
        SecurityContext.reset(tok)

def test_v100_gateway_and_openapi():
    async def _test():
        router = GatewayRouter()
        router.add_interceptor(CORSInterceptor())
        router.add_route("/v1/health", ["GET"], lambda ctx: ctx.response.json({"status": "GA_HEALTHY"}))

        req = GatewayRequest(method="GET", path="/v1/health")
        res = await router.dispatch(req)
        assert res.status_code == 200
        assert "GA_HEALTHY" in res.body

        gen = OpenAPIGenerator(title="Sarathi GA Spec", version="1.0.0")
        spec = gen.generate(router)
        assert spec["openapi"] == "3.1.0"
        assert spec["info"]["title"] == "Sarathi GA Spec"

    asyncio.run(_test())

def test_v100_auditor_production_readiness():
    auditor = HardeningAuditor()
    report = auditor.run_audit()
    assert report.is_production_ready is True
