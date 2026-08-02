"""HTTP middleware contracts and ordered pipeline composition."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from typing import Protocol, TypeAlias

from .request import Request
from .response import Response, StreamingResponse


HTTPResponse: TypeAlias = Response | StreamingResponse
MiddlewareResult: TypeAlias = HTTPResponse | Awaitable[HTTPResponse]


class NextHandler(Protocol):
    """Invoke the next middleware component or terminal HTTP handler."""

    def __call__(self, request: Request) -> MiddlewareResult: ...


class Middleware(Protocol):
    """Wrap an HTTP request handler with cross-cutting behaviour."""

    def __call__(self, request: Request, call_next: NextHandler) -> MiddlewareResult: ...


HTTPHandler: TypeAlias = Callable[[Request], MiddlewareResult]
MiddlewareCallable: TypeAlias = Callable[[Request, NextHandler], MiddlewareResult]


class MiddlewareOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MiddlewareExecution:
    """Describe one completed middleware invocation."""

    name: str
    index: int
    duration_seconds: float
    outcome: MiddlewareOutcome
    error: str | None = None


MiddlewareObserver: TypeAlias = Callable[
    [MiddlewareExecution], object | Awaitable[object]
]


class MiddlewarePipeline:
    """Compose middleware in declaration order around a terminal handler."""

    def __init__(
        self,
        middleware: Iterable[MiddlewareCallable] = (),
        *,
        observer: MiddlewareObserver | None = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        components = tuple(middleware)
        if any(not callable(component) for component in components):
            raise TypeError("Every HTTP middleware component must be callable.")
        if observer is not None and not callable(observer):
            raise TypeError("HTTP middleware observer must be callable.")
        if not callable(clock):
            raise TypeError("HTTP middleware clock must be callable.")
        self._middleware = components
        self._observer = observer
        self._clock = clock

    @property
    def middleware(self) -> tuple[MiddlewareCallable, ...]:
        return self._middleware

    def compose(self, handler: HTTPHandler) -> HTTPHandler:
        """Return one handler with this pipeline wrapped around *handler*."""

        if not callable(handler):
            raise TypeError("HTTP middleware terminal handler must be callable.")

        async def terminal(request: Request) -> HTTPResponse:
            return await self._resolve(handler(request), "HTTP handler")

        composed: HTTPHandler = terminal
        for index, component in reversed(tuple(enumerate(self._middleware))):
            following = composed
            component_name = getattr(component, "__name__", type(component).__name__)

            async def wrapped(
                request: Request,
                current: MiddlewareCallable = component,
                call_next: HTTPHandler = following,
                name: str = component_name,
                position: int = index,
            ) -> HTTPResponse:
                started = self._clock()
                outcome = MiddlewareOutcome.SUCCEEDED
                error_text: str | None = None
                try:
                    result = current(request, call_next)
                    return await self._resolve(result, "HTTP middleware")
                except Exception as error:
                    outcome = MiddlewareOutcome.FAILED
                    error_text = f"{type(error).__name__}: {error}"
                    raise
                finally:
                    await self._observe(
                        MiddlewareExecution(
                            name=name,
                            index=position,
                            duration_seconds=max(0.0, self._clock() - started),
                            outcome=outcome,
                            error=error_text,
                        )
                    )

            composed = wrapped
        return composed

    async def dispatch(self, request: Request, handler: HTTPHandler) -> HTTPResponse:
        """Run *request* through the composed pipeline and terminal handler."""

        return await self.compose(handler)(request)

    async def __call__(self, request: Request, handler: HTTPHandler) -> HTTPResponse:
        return await self.dispatch(request, handler)

    @staticmethod
    async def _resolve(result: MiddlewareResult, source: str) -> HTTPResponse:
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, (Response, StreamingResponse)):
            raise TypeError(f"{source} must return a Response or StreamingResponse.")
        return result

    async def _observe(self, execution: MiddlewareExecution) -> None:
        if self._observer is None:
            return
        try:
            result = self._observer(execution)
            if inspect.isawaitable(result):
                await result
        except Exception:
            # Diagnostics must never change request behaviour.
            pass
