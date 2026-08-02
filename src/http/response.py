"""HTTP response primitives and ASGI message generation."""

from __future__ import annotations

from collections.abc import AsyncIterable, Iterable
from typing import TypeAlias

from .contracts import ASGIMessage, ASGISend
from .exceptions import ResponseStreamError
from .headers import HeaderInput, Headers


def _body(value: bytes | bytearray | memoryview | str) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    raise TypeError("HTTP response body must be bytes-like or a string.")


class Response:
    """Immutable finite HTTP response."""

    def __init__(
        self,
        body: bytes | bytearray | memoryview | str = b"",
        *,
        status: int = 200,
        headers: HeaderInput = (),
        media_type: str | None = None,
    ) -> None:
        if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
            raise ValueError("HTTP response status must be an integer from 100 to 599.")
        encoded = _body(body)
        normalized = Headers(headers)
        if media_type is not None:
            if not media_type.strip():
                raise ValueError("HTTP response media type must not be blank.")
            normalized = normalized.with_default("content-type", media_type.strip())
        normalized = normalized.with_default("content-length", str(len(encoded)))
        self._body = encoded
        self._status = status
        self._headers = normalized

    @property
    def status(self) -> int:
        return self._status

    @property
    def body(self) -> bytes:
        return self._body

    @property
    def headers(self) -> Headers:
        return self._headers

    def start_message(self) -> ASGIMessage:
        return {
            "type": "http.response.start",
            "status": self.status,
            "headers": list(self.headers.raw),
        }

    def body_message(self) -> ASGIMessage:
        return {
            "type": "http.response.body",
            "body": self.body,
            "more_body": False,
        }

    async def send(self, send: ASGISend) -> None:
        await send(self.start_message())
        await send(self.body_message())


class TextResponse(Response):
    def __init__(
        self,
        text: str,
        *,
        status: int = 200,
        headers: HeaderInput = (),
    ) -> None:
        if not isinstance(text, str):
            raise TypeError("Text response content must be a string.")
        super().__init__(
            text,
            status=status,
            headers=headers,
            media_type="text/plain; charset=utf-8",
        )


StreamChunk: TypeAlias = bytes | bytearray | memoryview | str
StreamSource: TypeAlias = Iterable[StreamChunk] | AsyncIterable[StreamChunk]


class StreamingResponse:
    """Stream an iterable body without retaining the complete response."""

    def __init__(
        self,
        body: StreamSource,
        *,
        status: int = 200,
        headers: HeaderInput = (),
        media_type: str | None = None,
    ) -> None:
        if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
            raise ValueError("HTTP response status must be an integer from 100 to 599.")
        if not hasattr(body, "__iter__") and not hasattr(body, "__aiter__"):
            raise TypeError("Streaming response body must be iterable or async iterable.")
        normalized = Headers(headers)
        if media_type is not None:
            if not media_type.strip():
                raise ValueError("HTTP response media type must not be blank.")
            normalized = normalized.with_default("content-type", media_type.strip())
        self._body = body
        self._status = status
        self._headers = normalized

    @property
    def status(self) -> int:
        return self._status

    @property
    def headers(self) -> Headers:
        return self._headers

    def start_message(self) -> ASGIMessage:
        return {
            "type": "http.response.start",
            "status": self.status,
            "headers": list(self.headers.raw),
        }

    async def send(self, send: ASGISend) -> None:
        iterator = self._iterate().__aiter__()
        try:
            first = await anext(iterator)
        except StopAsyncIteration:
            await send(self.start_message())
            await send({"type": "http.response.body", "body": b"", "more_body": False})
            return
        except Exception as error:
            raise ResponseStreamError(
                f"Response stream failed before starting: {type(error).__name__}: {error}"
            ) from error
        await send(self.start_message())
        await send({"type": "http.response.body", "body": first, "more_body": True})
        try:
            async for chunk in iterator:
                await send(
                    {"type": "http.response.body", "body": chunk, "more_body": True}
                )
        except OSError:
            raise
        except Exception as error:
            raise ResponseStreamError(
                f"Response stream failed after starting: {type(error).__name__}: {error}"
            ) from error
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def _iterate(self):
        if hasattr(self._body, "__aiter__"):
            async for chunk in self._body:  # type: ignore[union-attr]
                yield self._chunk(chunk)
            return
        for chunk in self._body:  # type: ignore[union-attr]
            yield self._chunk(chunk)

    @staticmethod
    def _chunk(value: StreamChunk) -> bytes:
        try:
            return _body(value)
        except TypeError as error:
            raise ResponseStreamError(str(error)) from error
