"""Focused tests for M31 Pack 2 application, lifespan, and streaming."""

from __future__ import annotations

import asyncio

import pytest

from src.http import (
    ExceptionBoundary,
    HttpApplication,
    LifespanProtocolError,
    Response,
    ResponseStreamError,
    StreamingResponse,
    TextResponse,
    UnsupportedProtocolError,
)


def http_scope() -> dict[str, object]:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.5"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }


def receiver(*messages: dict[str, object]):
    pending = list(messages)

    async def receive() -> dict[str, object]:
        return pending.pop(0)

    return receive


async def collect_http(application: HttpApplication) -> list[dict[str, object]]:
    messages: list[dict[str, object]] = []

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    await application(
        http_scope(),
        receiver({"type": "http.request", "body": b""}),
        send,
    )
    return messages


def test_application_dispatches_request_and_finite_response() -> None:
    observed = []

    async def handler(request):
        observed.append((request.method, request.path))
        return TextResponse("ready", status=202)

    messages = asyncio.run(collect_http(HttpApplication(handler)))
    assert observed == [("GET", "/")]
    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 202
    assert messages[1] == {
        "type": "http.response.body",
        "body": b"ready",
        "more_body": False,
    }


def test_sync_handler_is_supported_without_special_adapter() -> None:
    messages = asyncio.run(
        collect_http(HttpApplication(lambda request: Response(request.method)))
    )
    assert messages[1]["body"] == b"GET"


def test_handler_failure_becomes_safe_internal_server_error() -> None:
    async def broken(request):
        del request
        raise RuntimeError("sensitive detail")

    messages = asyncio.run(collect_http(HttpApplication(broken)))
    assert messages[0]["status"] == 500
    assert messages[1]["body"] == b"Internal Server Error"
    assert b"sensitive" not in messages[1]["body"]


def test_debug_boundary_can_expose_error_deliberately() -> None:
    async def broken(request):
        del request
        raise ValueError("visible")

    application = HttpApplication(
        broken,
        exception_boundary=ExceptionBoundary(expose_errors=True),
    )
    messages = asyncio.run(collect_http(application))
    assert messages[1]["body"] == b"ValueError: visible"


def test_custom_async_exception_handler_controls_response() -> None:
    async def broken(request):
        del request
        raise LookupError("missing")

    async def recover(request, error):
        assert request.path == "/"
        assert isinstance(error, LookupError)
        return TextResponse("recovered", status=503)

    messages = asyncio.run(
        collect_http(
            HttpApplication(broken, exception_boundary=ExceptionBoundary(recover))
        )
    )
    assert messages[0]["status"] == 503
    assert messages[1]["body"] == b"recovered"


def test_invalid_handler_result_is_caught_by_error_boundary() -> None:
    messages = asyncio.run(collect_http(HttpApplication(lambda request: object())))
    assert messages[0]["status"] == 500


def test_server_disconnect_oserror_is_not_translated_to_second_response() -> None:
    application = HttpApplication(lambda request: Response("body"))

    async def send(message):
        del message
        raise OSError("connection closed")

    with pytest.raises(OSError, match="connection closed"):
        asyncio.run(
            application(
                http_scope(),
                receiver({"type": "http.request"}),
                send,
            )
        )


def test_application_rejects_unsupported_scope_types() -> None:
    application = HttpApplication(lambda request: Response())

    async def send(message):
        del message

    with pytest.raises(UnsupportedProtocolError, match="websocket"):
        asyncio.run(application({"type": "websocket"}, receiver(), send))


def test_streaming_response_sends_ordered_chunks_and_final_event() -> None:
    application = HttpApplication(
        lambda request: StreamingResponse(
            [b"one", "two"], media_type="text/plain; charset=utf-8"
        )
    )
    messages = asyncio.run(collect_http(application))
    assert [message["type"] for message in messages] == [
        "http.response.start",
        "http.response.body",
        "http.response.body",
        "http.response.body",
    ]
    assert [message.get("body") for message in messages[1:]] == [
        b"one",
        b"two",
        b"",
    ]
    assert [message["more_body"] for message in messages[1:]] == [True, True, False]


def test_async_and_empty_streams_are_supported() -> None:
    async def chunks():
        yield b"async"

    async_messages = asyncio.run(
        collect_http(HttpApplication(lambda request: StreamingResponse(chunks())))
    )
    assert async_messages[1]["body"] == b"async"
    empty_messages = asyncio.run(
        collect_http(HttpApplication(lambda request: StreamingResponse([])))
    )
    assert empty_messages[1] == {
        "type": "http.response.body",
        "body": b"",
        "more_body": False,
    }


def test_stream_failure_before_start_can_be_replaced_by_error_response() -> None:
    class Broken:
        def __iter__(self):
            raise RuntimeError("before")

    messages = asyncio.run(
        collect_http(HttpApplication(lambda request: StreamingResponse(Broken())))
    )
    assert len(messages) == 2
    assert messages[0]["status"] == 500


def test_stream_failure_after_start_is_reported_without_second_start() -> None:
    async def broken():
        yield b"first"
        raise RuntimeError("after")

    application = HttpApplication(lambda request: StreamingResponse(broken()))
    messages: list[dict[str, object]] = []

    async def send(message):
        messages.append(message)

    with pytest.raises(ResponseStreamError, match="after starting"):
        asyncio.run(
            application(
                http_scope(),
                receiver({"type": "http.request"}),
                send,
            )
        )
    assert [message["type"] for message in messages].count("http.response.start") == 1


def test_lifespan_runs_startup_and_reverse_shutdown_callbacks() -> None:
    events: list[str] = []

    async def async_start() -> None:
        events.append("start:async")

    application = HttpApplication(
        lambda request: Response(),
        startup=(lambda: events.append("start:sync"), async_start),
        shutdown=(lambda: events.append("stop:first"), lambda: events.append("stop:second")),
    )
    sent: list[dict[str, object]] = []

    async def send(message):
        sent.append(message)

    asyncio.run(
        application(
            {"type": "lifespan"},
            receiver({"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}),
            send,
        )
    )
    assert events == ["start:sync", "start:async", "stop:second", "stop:first"]
    assert sent == [
        {"type": "lifespan.startup.complete"},
        {"type": "lifespan.shutdown.complete"},
    ]
    assert application.started is False


def test_lifespan_reports_callback_failure_and_rejects_unknown_events() -> None:
    def broken() -> None:
        raise RuntimeError("startup failed")

    application = HttpApplication(lambda request: Response(), startup=(broken,))
    sent: list[dict[str, object]] = []

    async def send(message):
        sent.append(message)

    asyncio.run(
        application(
            {"type": "lifespan"},
            receiver({"type": "lifespan.startup"}),
            send,
        )
    )
    assert sent[0]["type"] == "lifespan.startup.failed"
    assert "startup failed" in sent[0]["message"]

    with pytest.raises(LifespanProtocolError, match="unknown"):
        asyncio.run(
            HttpApplication(lambda request: Response())(
                {"type": "lifespan"},
                receiver({"type": "lifespan.unknown"}),
                send,
            )
        )
