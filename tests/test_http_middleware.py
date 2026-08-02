"""Focused tests for M33 Pack 1 middleware contracts and composition."""

from __future__ import annotations

import asyncio

import pytest

from src.http import MiddlewarePipeline, Request, Response, StreamingResponse, TextResponse
from src.http import (
    ExceptionMiddleware,
    HttpApplication,
    MiddlewareOutcome,
    RequestIdMiddleware,
    TimingMiddleware,
    current_request_id,
)
from src.metrics import MetricsRegistry


async def receive() -> dict[str, object]:
    return {"type": "http.request", "body": b""}


def request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/middleware",
            "query_string": b"",
            "headers": [],
        },
        receive,
    )


def test_empty_pipeline_invokes_sync_terminal_handler() -> None:
    response = asyncio.run(
        MiddlewarePipeline().dispatch(request(), lambda current: TextResponse(current.path))
    )
    assert response.body == b"/middleware"


def test_middleware_wraps_handler_in_declaration_order() -> None:
    events: list[str] = []

    async def first(current, call_next):
        events.append("first:before")
        response = await call_next(current)
        events.append("first:after")
        return response

    async def second(current, call_next):
        events.append("second:before")
        response = await call_next(current)
        events.append("second:after")
        return response

    async def endpoint(current):
        events.append("handler")
        return Response()

    pipeline = MiddlewarePipeline((first, second))
    asyncio.run(pipeline.dispatch(request(), endpoint))
    assert events == [
        "first:before",
        "second:before",
        "handler",
        "second:after",
        "first:after",
    ]
    assert pipeline.middleware == (first, second)


def test_sync_and_async_middleware_can_be_combined() -> None:
    def sync_short_circuit(current, call_next):
        del current, call_next
        return TextResponse("cached", status=202)

    async def unreachable(current, call_next):
        return await call_next(current)

    response = asyncio.run(
        MiddlewarePipeline((sync_short_circuit, unreachable)).dispatch(
            request(), lambda current: TextResponse("endpoint")
        )
    )
    assert response.status == 202
    assert response.body == b"cached"


def test_pipeline_compose_returns_reusable_handler() -> None:
    visits: list[str] = []

    async def observe(current, call_next):
        visits.append(current.path)
        return await call_next(current)

    handler = MiddlewarePipeline((observe,)).compose(
        lambda current: StreamingResponse([current.path])
    )
    response = asyncio.run(handler(request()))
    assert isinstance(response, StreamingResponse)
    assert visits == ["/middleware"]


@pytest.mark.parametrize("source", ["HTTP handler", "HTTP middleware"])
def test_pipeline_rejects_invalid_response_results(source: str) -> None:
    if source == "HTTP handler":
        pipeline = MiddlewarePipeline()
        handler = lambda current: object()
    else:
        pipeline = MiddlewarePipeline((lambda current, call_next: object(),))
        handler = lambda current: Response()
    with pytest.raises(TypeError, match=source):
        asyncio.run(pipeline.dispatch(request(), handler))


def test_pipeline_validates_components_and_terminal_handler() -> None:
    with pytest.raises(TypeError, match="middleware component"):
        MiddlewarePipeline((object(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="terminal handler"):
        MiddlewarePipeline().compose(object())  # type: ignore[arg-type]


async def collect(application: HttpApplication) -> list[dict[str, object]]:
    sent: list[dict[str, object]] = []

    async def send(message: dict[str, object]) -> None:
        sent.append(message)

    await application(request().scope, receive, send)
    return sent


def test_http_application_executes_configured_middleware() -> None:
    events: list[str] = []

    async def observe(current, call_next):
        events.append("before")
        response = await call_next(current)
        events.append("after")
        return response.with_header("x-observed", "yes")

    application = HttpApplication(
        lambda current: TextResponse("endpoint"), middleware=(observe,)
    )
    messages = asyncio.run(collect(application))
    assert events == ["before", "after"]
    assert application.middleware == (observe,)
    assert (b"x-observed", b"yes") in messages[0]["headers"]


def test_http_application_middleware_can_short_circuit_route_handler() -> None:
    called = False

    def endpoint(current):
        nonlocal called
        called = True
        return Response()

    def cached(current, call_next):
        del current, call_next
        return TextResponse("cached", status=203)

    messages = asyncio.run(collect(HttpApplication(endpoint, middleware=(cached,))))
    assert called is False
    assert messages[0]["status"] == 203
    assert messages[1]["body"] == b"cached"


def test_exception_middleware_returns_safe_or_custom_response() -> None:
    def broken(current):
        raise RuntimeError("secret")

    safe = asyncio.run(
        MiddlewarePipeline((ExceptionMiddleware(),)).dispatch(request(), broken)
    )
    assert safe.status == 500
    assert safe.body == b"Internal Server Error"

    async def recover(current, error):
        assert current.path == "/middleware"
        assert isinstance(error, RuntimeError)
        return TextResponse("recovered", status=503)

    custom = asyncio.run(
        MiddlewarePipeline((ExceptionMiddleware(recover),)).dispatch(request(), broken)
    )
    assert custom.status == 503
    assert custom.body == b"recovered"


def test_exception_middleware_does_not_hide_transport_failures() -> None:
    def disconnected(current):
        raise OSError("disconnected")

    with pytest.raises(OSError, match="disconnected"):
        asyncio.run(
            MiddlewarePipeline((ExceptionMiddleware(),)).dispatch(
                request(), disconnected
            )
        )


def test_request_id_middleware_propagates_existing_identifier() -> None:
    current = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/existing",
            "query_string": b"",
            "headers": [(b"x-request-id", b"client-123")],
        },
        receive,
    )

    def endpoint(received):
        return TextResponse(current_request_id() or "missing")

    response = asyncio.run(
        MiddlewarePipeline((RequestIdMiddleware(),)).dispatch(current, endpoint)
    )
    assert response.body == b"client-123"
    assert response.headers.get_all("x-request-id") == ("client-123",)
    assert current_request_id() is None


def test_request_id_middleware_generates_identifier_and_mutates_stream() -> None:
    middleware = RequestIdMiddleware(identifier=lambda: "generated-456")
    response = asyncio.run(
        MiddlewarePipeline((middleware,)).dispatch(
            request(), lambda current: StreamingResponse([b"body"])
        )
    )
    assert isinstance(response, StreamingResponse)
    assert response.headers.get("x-request-id") == "generated-456"


def test_timing_middleware_adds_header_and_records_metric() -> None:
    readings = iter((10.0, 10.025))
    metrics = MetricsRegistry()
    middleware = TimingMiddleware(clock=lambda: next(readings), metrics=metrics)
    response = asyncio.run(
        MiddlewarePipeline((middleware,)).dispatch(
            request(), lambda current: Response()
        )
    )
    assert response.headers.get("server-timing") == "app;dur=25.000"
    labels = (("method", "GET"), ("outcome", "succeeded"))
    sample = metrics.snapshot().find("http.middleware.duration_seconds", labels)
    assert sample is not None
    assert sample.value == pytest.approx(0.025)


def test_pipeline_instrumentation_records_order_duration_and_failure() -> None:
    executions = []
    ticks = iter((1.0, 2.0, 4.0, 7.0))

    async def first(current, call_next):
        return await call_next(current)

    async def second(current, call_next):
        del current, call_next
        raise LookupError("missing")

    pipeline = MiddlewarePipeline(
        (first, second), observer=executions.append, clock=lambda: next(ticks)
    )
    with pytest.raises(LookupError, match="missing"):
        asyncio.run(pipeline.dispatch(request(), lambda current: Response()))
    assert [(item.name, item.index) for item in executions] == [
        ("second", 1),
        ("first", 0),
    ]
    assert all(item.outcome is MiddlewareOutcome.FAILED for item in executions)
    assert executions[0].error == "LookupError: missing"
    assert executions[0].duration_seconds == 2.0
    assert executions[1].duration_seconds == 6.0


def test_instrumentation_failure_is_isolated_from_response() -> None:
    def broken_observer(execution):
        raise RuntimeError("diagnostics unavailable")

    response = asyncio.run(
        MiddlewarePipeline(
            (lambda current, call_next: call_next(current),),
            observer=broken_observer,
        ).dispatch(request(), lambda current: Response("ok"))
    )
    assert response.body == b"ok"


def test_response_header_mutation_replaces_or_appends_predictably() -> None:
    original = Response("body", headers=(("x-mode", "old"),))
    replaced = original.with_header("x-mode", "new")
    appended = replaced.with_header("x-mode", "extra", replace=False)
    assert original.headers.get_all("x-mode") == ("old",)
    assert replaced.headers.get_all("x-mode") == ("new",)
    assert appended.headers.get_all("x-mode") == ("new", "extra")


def test_builtin_middleware_configuration_is_validated() -> None:
    with pytest.raises(TypeError, match="exception handler"):
        ExceptionMiddleware(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="header name"):
        RequestIdMiddleware(header=" ")
    with pytest.raises(TypeError, match="generator"):
        RequestIdMiddleware(identifier=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="clock"):
        TimingMiddleware(clock=object())  # type: ignore[arg-type]
