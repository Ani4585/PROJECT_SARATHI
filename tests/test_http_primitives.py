"""Focused tests for M31 Pack 1 HTTP and ASGI primitives."""

from __future__ import annotations

import asyncio

import pytest

from src.http import (
    ClientDisconnectedError,
    Headers,
    InvalidMessageError,
    InvalidScopeError,
    Request,
    RequestBodyTooLargeError,
    Response,
    TextResponse,
)


def scope(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.5"},
        "http_version": "1.1",
        "method": "get",
        "scheme": "https",
        "path": "/items",
        "raw_path": b"/items",
        "query_string": b"tag=one&tag=two&empty=",
        "headers": [(b"host", b"example.test"), (b"x-id", b"one")],
        "client": ("127.0.0.1", 5000),
        "server": ("example.test", 443),
    }
    value.update(overrides)
    return value


def receive_messages(*messages: dict[str, object]):
    pending = list(messages)

    async def receive() -> dict[str, object]:
        return pending.pop(0)

    return receive


def test_headers_preserve_order_duplicates_and_case_insensitive_lookup() -> None:
    headers = Headers(
        [("Set-Cookie", "first=1"), (b"set-cookie", b"second=2"), ("X-ID", "7")]
    )
    assert headers.raw == (
        (b"set-cookie", b"first=1"),
        (b"set-cookie", b"second=2"),
        (b"x-id", b"7"),
    )
    assert headers.get("SET-COOKIE") == "first=1"
    assert headers.get_all("set-cookie") == ("first=1", "second=2")
    assert "x-id" in headers


def test_headers_reject_invalid_names_and_line_breaks() -> None:
    with pytest.raises(ValueError, match="token"):
        Headers([("bad header", "value")])
    with pytest.raises(ValueError, match="line breaks"):
        Headers([("x-value", "safe\r\ninjected")])


def test_request_validates_and_normalizes_scope_metadata() -> None:
    request = Request(scope(), receive_messages({"type": "http.request"}))
    assert request.method == "GET"
    assert request.path == "/items"
    assert request.scheme == "https"
    assert request.http_version == "1.1"
    assert request.query_params == (("tag", "one"), ("tag", "two"), ("empty", ""))
    assert request.headers.get("host") == "example.test"
    assert request.client == ("127.0.0.1", 5000)


def test_request_rejects_non_http_and_malformed_scopes() -> None:
    receive = receive_messages({"type": "http.request"})
    with pytest.raises(InvalidScopeError, match="type"):
        Request(scope(type="websocket"), receive)
    with pytest.raises(InvalidScopeError, match="method"):
        Request(scope(method=""), receive)
    with pytest.raises(InvalidScopeError, match="absolute path"):
        Request(scope(path="relative"), receive)
    with pytest.raises(InvalidScopeError, match="query_string"):
        Request(scope(query_string="bad"), receive)


def test_request_collects_chunked_body_once_and_caches_it() -> None:
    calls = 0
    messages = [
        {"type": "http.request", "body": b"hello ", "more_body": True},
        {"type": "http.request", "body": b"world", "more_body": False},
    ]

    async def receive() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return messages.pop(0)

    request = Request(scope(method="POST"), receive)
    assert asyncio.run(request.body()) == b"hello world"
    assert asyncio.run(request.body()) == b"hello world"
    assert calls == 2


def test_request_enforces_body_limit_before_caching() -> None:
    request = Request(
        scope(method="POST"),
        receive_messages({"type": "http.request", "body": b"12345"}),
    )
    with pytest.raises(RequestBodyTooLargeError, match="4-byte"):
        asyncio.run(request.body(max_bytes=4))


def test_cached_request_body_still_honors_a_smaller_later_limit() -> None:
    request = Request(
        scope(method="POST"),
        receive_messages({"type": "http.request", "body": b"12345"}),
    )
    assert asyncio.run(request.body(max_bytes=5)) == b"12345"
    with pytest.raises(RequestBodyTooLargeError, match="4-byte"):
        asyncio.run(request.body(max_bytes=4))


def test_request_reports_disconnect_before_complete_body() -> None:
    request = Request(
        scope(method="POST"),
        receive_messages({"type": "http.disconnect"}),
    )
    with pytest.raises(ClientDisconnectedError, match="disconnected"):
        asyncio.run(request.body())


def test_request_rejects_unexpected_events_and_non_byte_chunks() -> None:
    unexpected = Request(
        scope(method="POST"),
        receive_messages({"type": "websocket.receive"}),
    )
    with pytest.raises(InvalidMessageError, match="Expected"):
        asyncio.run(unexpected.body())
    invalid_body = Request(
        scope(method="POST"),
        receive_messages({"type": "http.request", "body": "text"}),
    )
    with pytest.raises(InvalidMessageError, match="must be bytes"):
        asyncio.run(invalid_body.body())


def test_response_generates_ordered_asgi_start_and_body_messages() -> None:
    response = Response(
        b"hello",
        status=201,
        headers=[("x-id", "7")],
        media_type="application/octet-stream",
    )
    assert response.start_message() == {
        "type": "http.response.start",
        "status": 201,
        "headers": [
            (b"x-id", b"7"),
            (b"content-type", b"application/octet-stream"),
            (b"content-length", b"5"),
        ],
    }
    assert response.body_message() == {
        "type": "http.response.body",
        "body": b"hello",
        "more_body": False,
    }


def test_response_preserves_explicit_content_headers() -> None:
    response = Response(
        "body",
        headers=[("content-length", "99"), ("content-type", "custom/type")],
        media_type="ignored/type",
    )
    assert response.headers.get("content-length") == "99"
    assert response.headers.get("content-type") == "custom/type"


def test_text_response_encodes_unicode_and_content_type() -> None:
    response = TextResponse("Sārathi")
    assert response.body == "Sārathi".encode("utf-8")
    assert response.headers.get("content-type") == "text/plain; charset=utf-8"
    assert response.headers.get("content-length") == str(len(response.body))


def test_response_rejects_invalid_status_body_and_media_type() -> None:
    with pytest.raises(ValueError, match="100 to 599"):
        Response(status=99)
    with pytest.raises(TypeError, match="bytes-like"):
        Response(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="media type"):
        Response(media_type=" ")
