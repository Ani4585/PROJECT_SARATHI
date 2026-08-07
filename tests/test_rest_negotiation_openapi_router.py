"""Tests for REST response serialization, OpenApiGenerator, and RestControllerRouter."""

import asyncio
import json
import pytest

from src.http import Request, Response
from src.rest import (
    ContentNegotiator,
    OpenApiGenerator,
    ProblemDetails,
    RestControllerRouter,
    controller,
    get,
    post,
)


@controller("/api/users")
class UserController:
    @get("")
    def list_users(self, search: str = "all"):
        return [{"id": 1, "name": "Sarathi", "search": search}]

    @get("/{id}")
    def get_user(self, id: str):
        return {"id": id, "name": "User " + id}

    @post("")
    def create_user(self, payload: dict):
        return {"status": "created", "data": payload}


def test_content_negotiator_problem_details_and_json() -> None:
    problem = ProblemDetails(title="Not Found", status=404, detail="Resource missing")
    res = ContentNegotiator.serialize(problem)
    assert res.status == 404
    assert res.headers.get("content-type") == "application/problem+json"

    data_res = ContentNegotiator.serialize({"status": "ok"})
    assert data_res.status == 200
    assert data_res.headers.get("content-type") == "application/json"


def test_openapi_generator_schema_extraction() -> None:
    generator = OpenApiGenerator(title="Test REST API", version="0.8.23")
    generator.register_controller(UserController)

    schema = generator.generate_schema()
    assert schema["openapi"] == "3.0.3"
    assert schema["info"]["title"] == "Test REST API"
    assert "/api/users" in schema["paths"]
    assert "get" in schema["paths"]["/api/users"]
    assert "post" in schema["paths"]["/api/users"]


def test_rest_controller_router_dispatch_and_binding() -> None:
    async def run_test():
        router = RestControllerRouter()
        router.register(UserController)
        ctrl = UserController()

        async def dummy_receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        # Test GET /api/users
        req1 = Request({"type": "http", "method": "GET", "path": "/api/users", "query_string": b"search=active"}, dummy_receive)
        res1 = await router.handle_request(req1, ctrl, ctrl.list_users)
        assert res1.status == 200
        data1 = json.loads(res1.body.decode("utf-8"))
        assert data1[0]["search"] == "active"

        # Test POST /api/users with JSON payload
        json_bytes = json.dumps({"name": "NewUser"}).encode("utf-8")
        async def json_receive():
            return {"type": "http.request", "body": json_bytes, "more_body": False}

        req2 = Request({"type": "http", "method": "POST", "path": "/api/users"}, json_receive)
        res2 = await router.handle_request(req2, ctrl, ctrl.create_user)
        assert res2.status == 200
        data2 = json.loads(res2.body.decode("utf-8"))
        assert data2["data"]["name"] == "NewUser"

    asyncio.run(run_test())
