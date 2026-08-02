"""ASGI and HTTP callable contracts."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Protocol, TypeAlias


ASGIScope: TypeAlias = Mapping[str, object]
ASGIMessage: TypeAlias = dict[str, object]
ASGIReceive: TypeAlias = Callable[[], Awaitable[ASGIMessage]]
ASGISend: TypeAlias = Callable[[ASGIMessage], Awaitable[None]]


class ASGIApplication(Protocol):
    async def __call__(
        self,
        scope: ASGIScope,
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None: ...


class HTTPHandler(Protocol):
    async def __call__(self, request: object) -> object: ...


class ServerAdapter(Protocol):
    def run(self, application: ASGIApplication) -> None: ...
