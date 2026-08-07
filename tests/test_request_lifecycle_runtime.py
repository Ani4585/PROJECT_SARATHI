"""Tests for runtime finalization, cancellation, tracing, and streaming edge cases."""

from __future__ import annotations

import asyncio
import pytest

from src.http import (
    ClientDisconnectedError,
    HttpApplication,
    Request,
    Response,
    StreamingResponse,
    TextResponse,
    current_span_id,
    current_trace_id,
)


def test_response_finalization_and_tracing_header_injection() -> None:
    async def handler(req: Request) -> Response:
        return TextResponse("hello world")

    app = HttpApplication(handler)
    sent_messages: list[dict] = []

    async def dummy_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def dummy_send(msg):
        sent_messages.append(msg)

    scope = {"type": "http", "method": "GET", "path": "/"}
    asyncio.run(app(scope, dummy_receive, dummy_send))

    assert len(sent_messages) == 2
    headers = dict(sent_messages[0]["headers"])
    assert b"x-request-id" in headers
    assert b"x-trace-id" in headers


def test_cancellation_and_client_disconnect_signal() -> None:
    async def handler(req: Request) -> Response:
        await req.body()
        return TextResponse("ok")

    app = HttpApplication(handler)

    async def disconnect_receive():
        return {"type": "http.disconnect"}

    async def dummy_send(msg):
        pass

    scope = {"type": "http", "method": "POST", "path": "/"}
    with pytest.raises(ClientDisconnectedError):
        asyncio.run(app(scope, disconnect_receive, dummy_send))


def test_streaming_response_finalization() -> None:
    async def chunk_generator():
        yield b"chunk1"
        yield b"chunk2"

    async def handler(req: Request) -> StreamingResponse:
        return StreamingResponse(chunk_generator(), status=200)

    app = HttpApplication(handler)
    sent_messages: list[dict] = []

    async def dummy_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def dummy_send(msg):
        sent_messages.append(msg)

    scope = {"type": "http", "method": "GET", "path": "/stream"}
    asyncio.run(app(scope, dummy_receive, dummy_send))

    assert len(sent_messages) == 4  # start, body1, body2, final empty body
    headers = dict(sent_messages[0]["headers"])
    assert b"x-request-id" in headers
    assert b"x-trace-id" in headers
