"""ASGI HTTP application dispatch, lifespan, and error boundaries."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from typing import TypeAlias

from .contracts import ASGIMessage, ASGIReceive, ASGIScope, ASGISend
from .exceptions import (
    InvalidMessageError,
    LifespanProtocolError,
    ResponseStreamError,
    UnsupportedProtocolError,
)
from .middleware import MiddlewareCallable, MiddlewarePipeline
from .request import Request
from .response import Response, StreamingResponse, TextResponse


HTTPResponse: TypeAlias = Response | StreamingResponse
Handler: TypeAlias = Callable[[Request], HTTPResponse | Awaitable[HTTPResponse]]
ErrorHandler: TypeAlias = Callable[
    [Request, Exception], HTTPResponse | Awaitable[HTTPResponse]
]
LifecycleCallback: TypeAlias = Callable[[], object | Awaitable[object]]


class ExceptionBoundary:
    """Translate pre-response application failures into safe HTTP responses."""

    def __init__(
        self,
        handler: ErrorHandler | None = None,
        *,
        expose_errors: bool = False,
    ) -> None:
        self._handler = handler
        self._expose_errors = bool(expose_errors)

    async def response(self, request: Request, error: Exception) -> HTTPResponse:
        if self._handler is not None:
            candidate = self._handler(request, error)
            if inspect.isawaitable(candidate):
                candidate = await candidate
            if not isinstance(candidate, (Response, StreamingResponse)):
                raise TypeError("HTTP exception handler must return a response.")
            return candidate
        text = (
            f"{type(error).__name__}: {error}"
            if self._expose_errors
            else "Internal Server Error"
        )
        return TextResponse(text, status=500)


class _TrackedSender:
    def __init__(self, send: ASGISend) -> None:
        self._send = send
        self.started = False

    async def __call__(self, message: ASGIMessage) -> None:
        if message.get("type") == "http.response.start":
            self.started = True
        await self._send(message)


class HttpApplication:
    """Single-callable ASGI application for HTTP and lifespan scopes."""

    def __init__(
        self,
        handler: Handler,
        *,
        startup: Sequence[LifecycleCallback] = (),
        shutdown: Sequence[LifecycleCallback] = (),
        exception_boundary: ExceptionBoundary | None = None,
        middleware: Iterable[MiddlewareCallable] = (),
    ) -> None:
        if not callable(handler):
            raise TypeError("HTTP application handler must be callable.")
        if any(not callable(callback) for callback in (*startup, *shutdown)):
            raise TypeError("HTTP lifecycle callbacks must be callable.")
        self._middleware = MiddlewarePipeline(middleware)
        self._handler = self._middleware.compose(handler)
        self._startup = tuple(startup)
        self._shutdown = tuple(shutdown)
        self._boundary = exception_boundary or ExceptionBoundary()
        self.state: dict[str, object] = {}
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    @property
    def middleware(self) -> tuple[MiddlewareCallable, ...]:
        return self._middleware.middleware

    async def __call__(
        self,
        scope: ASGIScope,
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None:
        scope_type = scope.get("type")
        if scope_type == "http":
            await self._dispatch_http(scope, receive, send)
            return
        if scope_type == "lifespan":
            await self._dispatch_lifespan(receive, send)
            return
        raise UnsupportedProtocolError(f"Unsupported ASGI scope type: {scope_type!r}")

    async def _dispatch_http(
        self,
        scope: ASGIScope,
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None:
        request = Request(scope, receive)
        tracked = _TrackedSender(send)
        try:
            response = self._handler(request)
            if inspect.isawaitable(response):
                response = await response
            if not isinstance(response, (Response, StreamingResponse)):
                raise TypeError("HTTP handler must return a Response or StreamingResponse.")
            await response.send(tracked)
        except OSError:
            raise
        except Exception as error:
            if tracked.started:
                if isinstance(error, ResponseStreamError):
                    raise
                raise ResponseStreamError(
                    f"HTTP response failed after starting: {type(error).__name__}: {error}"
                ) from error
            fallback = await self._boundary.response(request, error)
            await fallback.send(tracked)

    async def _dispatch_lifespan(
        self,
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None:
        while True:
            message = await receive()
            message_type = message.get("type")
            if message_type == "lifespan.startup":
                try:
                    await self._run_callbacks(self._startup)
                except Exception as error:
                    await send(
                        {
                            "type": "lifespan.startup.failed",
                            "message": f"{type(error).__name__}: {error}",
                        }
                    )
                    return
                self._started = True
                await send({"type": "lifespan.startup.complete"})
            elif message_type == "lifespan.shutdown":
                try:
                    await self._run_callbacks(tuple(reversed(self._shutdown)))
                except Exception as error:
                    await send(
                        {
                            "type": "lifespan.shutdown.failed",
                            "message": f"{type(error).__name__}: {error}",
                        }
                    )
                    return
                self._started = False
                await send({"type": "lifespan.shutdown.complete"})
                return
            else:
                raise LifespanProtocolError(
                    f"Unsupported lifespan message: {message_type!r}"
                )

    @staticmethod
    async def _run_callbacks(callbacks: Sequence[LifecycleCallback]) -> None:
        for callback in callbacks:
            result = callback()
            if inspect.isawaitable(result):
                await result
