"""Tests for RequestContext, HTTP scope, and request body/query/header parsing."""

from __future__ import annotations

import asyncio
import json
import pytest

from src.http import HttpContext, InvalidMessageError, Request, RequestContext


def test_request_context_properties_and_state() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "headers": [(b"x-request-id", b"req-123"), (b"x-trace-id", b"trace-abc")],
        "state": {"initial_key": "initial_value"},
    }

    async def dummy_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    req = Request(scope, dummy_receive)
    ctx = req.context

    assert isinstance(ctx, RequestContext)
    assert isinstance(ctx, HttpContext)
    assert ctx.request is req
    assert ctx.request_id == "req-123"
    assert ctx.trace_id == "trace-abc"
    assert ctx.elapsed_ms >= 0.0
    assert ctx["initial_key"] == "initial_value"

    ctx["user_id"] = 42
    assert ctx.get("user_id") == 42
    assert "user_id" in ctx


def test_request_context_cancellation() -> None:
    scope = {"type": "http", "method": "GET", "path": "/"}

    async def dummy_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    req = Request(scope, dummy_receive)
    ctx = req.context

    assert not ctx.is_cancelled
    assert not ctx.is_disconnected

    ctx.cancel()

    assert ctx.is_cancelled
    assert ctx.is_disconnected


def test_request_header_path_and_query_helpers() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/users/10",
        "query_string": b"search=sarathi&limit=5",
        "headers": [(b"content-type", b"application/json")],
        "path_params": {"user_id": "10"},
    }

    async def dummy_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    req = Request(scope, dummy_receive)

    assert req.header("content-type") == "application/json"
    assert req.header("missing", "default_val") == "default_val"
    assert req.path_params == {"user_id": "10"}
    assert req.query_dict == {"search": "sarathi", "limit": "5"}
    assert req.query_param("search") == "sarathi"
    assert req.query_param("missing", "none") == "none"


def test_request_json_text_and_form_parsing() -> None:
    data = {"name": "Sarathi", "role": "framework"}
    json_bytes = json.dumps(data).encode("utf-8")

    async def receive_json():
        return {"type": "http.request", "body": json_bytes, "more_body": False}

    req = Request({"type": "http", "method": "POST", "path": "/"}, receive_json)

    assert asyncio.run(req.text()) == json.dumps(data)
    assert asyncio.run(req.json()) == data

    form_bytes = b"title=Project&status=active"

    async def receive_form():
        return {"type": "http.request", "body": form_bytes, "more_body": False}

    req_form = Request({"type": "http", "method": "POST", "path": "/"}, receive_form)
    assert asyncio.run(req_form.form()) == (("title", "Project"), ("status", "active"))


def test_malformed_json_raises_invalid_message_error() -> None:
    async def receive_bad_json():
        return {"type": "http.request", "body": b"{bad_json: ", "more_body": False}

    req = Request({"type": "http", "method": "POST", "path": "/"}, receive_bad_json)

    with pytest.raises(InvalidMessageError, match="Malformed JSON payload"):
        asyncio.run(req.json())


def test_empty_json_raises_invalid_message_error() -> None:
    async def receive_empty():
        return {"type": "http.request", "body": b"   ", "more_body": False}

    req = Request({"type": "http", "method": "POST", "path": "/"}, receive_empty)

    with pytest.raises(InvalidMessageError, match="Cannot parse JSON from an empty request body"):
        asyncio.run(req.json())
