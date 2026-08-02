"""ASGI HTTP request primitive."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import MappingProxyType
from urllib.parse import parse_qsl

from .contracts import ASGIReceive, ASGIScope
from .exceptions import (
    ClientDisconnectedError,
    InvalidMessageError,
    InvalidScopeError,
    RequestBodyTooLargeError,
)
from .headers import Headers


class Request:
    """Validated immutable request metadata with bounded body collection."""

    def __init__(self, scope: ASGIScope, receive: ASGIReceive) -> None:
        if scope.get("type") != "http":
            raise InvalidScopeError("Request scope type must be 'http'.")
        method = scope.get("method")
        path = scope.get("path")
        query_string = scope.get("query_string", b"")
        raw_headers = scope.get("headers", ())
        if not isinstance(method, str) or not method.strip():
            raise InvalidScopeError("HTTP scope method must be a non-blank string.")
        if not isinstance(path, str) or not path.startswith("/"):
            raise InvalidScopeError("HTTP scope path must be an absolute path string.")
        if not isinstance(query_string, bytes):
            raise InvalidScopeError("HTTP scope query_string must be bytes.")
        if not callable(receive):
            raise TypeError("ASGI receive must be callable.")
        try:
            headers = Headers(raw_headers)  # type: ignore[arg-type]
        except (TypeError, ValueError) as error:
            raise InvalidScopeError(f"HTTP scope headers are invalid: {error}") from error
        normalized = dict(scope)
        normalized["method"] = method.strip().upper()
        normalized["path"] = path
        normalized["query_string"] = query_string
        normalized["headers"] = headers.raw
        self._scope = MappingProxyType(normalized)
        self._receive = receive
        self._headers = headers
        self._body: bytes | None = None
        self._body_lock = asyncio.Lock()

    @property
    def scope(self) -> Mapping[str, object]:
        return self._scope

    @property
    def method(self) -> str:
        return str(self._scope["method"])

    @property
    def path(self) -> str:
        return str(self._scope["path"])

    @property
    def scheme(self) -> str:
        return str(self._scope.get("scheme", "http"))

    @property
    def http_version(self) -> str:
        return str(self._scope.get("http_version", "1.1"))

    @property
    def query_string(self) -> bytes:
        return self._scope["query_string"]  # type: ignore[return-value]

    @property
    def query_params(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            parse_qsl(
                self.query_string.decode("utf-8", errors="replace"),
                keep_blank_values=True,
            )
        )

    @property
    def headers(self) -> Headers:
        return self._headers

    @property
    def client(self) -> tuple[str, int] | None:
        value = self._scope.get("client")
        return value if isinstance(value, tuple) and len(value) == 2 else None  # type: ignore[return-value]

    async def body(self, *, max_bytes: int = 1024 * 1024) -> bytes:
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 0:
            raise ValueError("Request body limit must be a non-negative integer.")
        if self._body is not None:
            if len(self._body) > max_bytes:
                raise RequestBodyTooLargeError(
                    f"Request body exceeds the {max_bytes}-byte limit."
                )
            return self._body
        async with self._body_lock:
            if self._body is not None:
                if len(self._body) > max_bytes:
                    raise RequestBodyTooLargeError(
                        f"Request body exceeds the {max_bytes}-byte limit."
                    )
                return self._body
            chunks: list[bytes] = []
            size = 0
            while True:
                message = await self._receive()
                message_type = message.get("type")
                if message_type == "http.disconnect":
                    raise ClientDisconnectedError(
                        "Client disconnected before the request body completed."
                    )
                if message_type != "http.request":
                    raise InvalidMessageError(
                        f"Expected 'http.request', received {message_type!r}."
                    )
                chunk = message.get("body", b"")
                if not isinstance(chunk, bytes):
                    raise InvalidMessageError("HTTP request body chunks must be bytes.")
                size += len(chunk)
                if size > max_bytes:
                    raise RequestBodyTooLargeError(
                        f"Request body exceeds the {max_bytes}-byte limit."
                    )
                chunks.append(chunk)
                if not bool(message.get("more_body", False)):
                    break
            self._body = b"".join(chunks)
            return self._body
