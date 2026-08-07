"""Tests for Web Dependency Injection, RequestScope lifetime, and scope disposal."""

from __future__ import annotations

import asyncio
import pytest

from src.container import RequestScope, ServiceContainer, ServiceLifetime
from src.http import HttpApplication, Request, RequestContext, Response, TextResponse, inject_handler


class ScopedDatabaseService:
    def __init__(self) -> None:
        self.disposed = False

    def dispose(self) -> None:
        self.disposed = True


def test_web_di_request_scope_binding_and_disposal() -> None:
    container = ServiceContainer()
    container.register_scoped(ScopedDatabaseService)

    db_instances: list[ScopedDatabaseService] = []

    async def handler(req: Request) -> Response:
        scope: RequestScope = req.scope["request_scope"]
        db = container.build(ScopedDatabaseService)
        scope.set(ScopedDatabaseService, db)
        db_instances.append(db)
        return TextResponse("ok")

    app = HttpApplication(handler, container=container)

    async def dummy_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def dummy_send(msg):
        pass

    scope = {"type": "http", "method": "GET", "path": "/"}
    asyncio.run(app(scope, dummy_receive, dummy_send))

    assert len(db_instances) == 1
    assert db_instances[0].disposed  # Guaranteed scope disposal!


def test_concurrent_requests_get_isolated_scoped_services() -> None:
    container = ServiceContainer()
    container.register_scoped(ScopedDatabaseService)

    db_map: dict[str, ScopedDatabaseService] = {}

    async def handler(req: Request) -> Response:
        req_id = req.context.request_id
        scope: RequestScope = req.scope["request_scope"]
        db = container.build(ScopedDatabaseService)
        scope.set(ScopedDatabaseService, db)
        db_map[req_id] = db
        return TextResponse(req_id)

    app = HttpApplication(handler, container=container)

    async def run_concurrent():
        async def make_req(req_id: str):
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(msg):
                pass

            scope = {"type": "http", "method": "GET", "path": "/", "headers": [(b"x-request-id", req_id.encode())]}
            await app(scope, receive, send)

        await asyncio.gather(make_req("req-1"), make_req("req-2"))

    asyncio.run(run_concurrent())

    assert len(db_map) == 2
    assert db_map["req-1"] is not db_map["req-2"]  # Concurrent request isolation!
    assert db_map["req-1"].disposed
    assert db_map["req-2"].disposed


def test_inject_handler_helper() -> None:
    container = ServiceContainer()
    container.register_scoped(ScopedDatabaseService)

    async def raw_handler(req: Request, db: ScopedDatabaseService) -> Response:
        assert isinstance(db, ScopedDatabaseService)
        return TextResponse("injected")

    di_handler = inject_handler(raw_handler, container)
    app = HttpApplication(di_handler, container=container)

    async def dummy_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    sent = []
    async def dummy_send(msg):
        sent.append(msg)

    scope = {"type": "http", "method": "GET", "path": "/"}
    asyncio.run(app(scope, dummy_receive, dummy_send))

    assert len(sent) == 2
