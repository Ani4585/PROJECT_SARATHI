import asyncio

class CancellationToken:
    def __init__(self) -> None:
        self._is_cancelled = False

    @property
    def is_cancellation_requested(self) -> bool:
        return self._is_cancelled

    @property
    def isCancellationRequested(self) -> bool:
        return self._is_cancelled

    def cancel(self) -> None:
        self._is_cancelled = True

    def throw_if_cancellation_requested(self) -> None:
        if self._is_cancelled:
            raise asyncio.CancelledError("Operation was cancelled by CancellationToken")

    def throwIfCancellationRequested(self) -> None:
        self.throw_if_cancellation_requested()
