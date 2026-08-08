import asyncio
import json
import pytest
from sarathi.gateway import (
    GatewayRequest,
    GatewayResponse,
    GatewayContext,
    GatewayRouter,
    CORSInterceptor,
    LoggingInterceptor,
    AuthInterceptor,
    OpenAPIGenerator,
)

def test_gateway_route_dispatch_and_parameter_extraction():
    async def _test():
        router = GatewayRouter()

        def get_user(ctx, user_id):
            return ctx.response.json({"user_id": user_id, "status": "active"})

        router.add_route("/api/v1/users/{user_id}", ["GET"], get_user, name="get_user")

        req = GatewayRequest(method="GET", path="/api/v1/users/42")
        res = await router.dispatch(req)

        assert res.status_code == 200
        assert "42" in res.body
        assert "active" in res.body

    asyncio.run(_test())

def test_cors_interceptor_preflight():
    async def _test():
        router = GatewayRouter()
        cors = CORSInterceptor(allow_origins=["http://localhost:3000"])
        router.add_interceptor(cors)

        req = GatewayRequest(method="OPTIONS", path="/api/v1/resource", headers={"origin": "http://localhost:3000"})
        res = await router.dispatch(req)

        assert res.status_code == 204
        assert res.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert "GET" in res.headers["Access-Control-Allow-Methods"]

    asyncio.run(_test())

def test_logging_interceptor():
    async def _test():
        router = GatewayRouter()
        logger = LoggingInterceptor()
        router.add_interceptor(logger)

        router.add_route("/ping", ["GET"], lambda ctx: ctx.response.json({"msg": "pong"}))

        req = GatewayRequest(method="GET", path="/ping")
        res = await router.dispatch(req)

        assert res.status_code == 200
        assert len(logger.logs) == 2
        assert "INBOUND GET /ping" in logger.logs[0]

    asyncio.run(_test())

def test_auth_interceptor_unauthorized():
    async def _test():
        router = GatewayRouter()
        auth = AuthInterceptor(token_verifier=True)
        router.add_interceptor(auth)

        router.add_route("/secure", ["GET"], lambda ctx: ctx.response.json({"ok": True}))

        req = GatewayRequest(method="GET", path="/secure")
        res = await router.dispatch(req)

        assert res.status_code == 401
        assert "Unauthorized" in res.body

    asyncio.run(_test())

def test_gateway_404_not_found():
    async def _test():
        router = GatewayRouter()
        req = GatewayRequest(method="GET", path="/nonexistent")
        res = await router.dispatch(req)

        assert res.status_code == 404
        assert "Route Not Found" in res.body

    asyncio.run(_test())

def test_openapi_generator():
    router = GatewayRouter()
    router.add_route("/api/v1/orders/{order_id}", ["GET", "POST"], lambda ctx, order_id: None, name="order_handler")

    generator = OpenAPIGenerator(title="Order Gateway API", version="1.0.0")
    spec = generator.generate(router)

    assert spec["openapi"] == "3.1.0"
    assert spec["info"]["title"] == "Order Gateway API"
    assert "/api/v1/orders/{order_id}" in spec["paths"]
    assert "get" in spec["paths"]["/api/v1/orders/{order_id}"]
    assert "post" in spec["paths"]["/api/v1/orders/{order_id}"]
