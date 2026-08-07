"""PROJECT SARATHI Request Scope and Resource Disposal."""

from __future__ import annotations

import inspect
from typing import Any


class RequestScope:
    """Request-scoped dependency lifetime container and resource manager."""

    def __init__(self, parent_container: Any = None) -> None:
        self.parent_container = parent_container
        self._instances: dict[Any, Any] = {}
        self._disposables: list[Any] = []
        self._is_disposed = False

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    def get(self, key: Any) -> Any:
        return self._instances.get(key)

    def set(self, key: Any, instance: Any) -> None:
        self._instances[key] = instance
        if hasattr(instance, "close") or hasattr(instance, "dispose") or hasattr(instance, "__aexit__"):
            if instance not in self._disposables:
                self._disposables.append(instance)

    def register_disposable(self, item: Any) -> None:
        if item not in self._disposables:
            self._disposables.append(item)

    async def dispose(self) -> None:
        if self._is_disposed:
            return
        self._is_disposed = True
        for item in reversed(self._disposables):
            try:
                if hasattr(item, "dispose"):
                    res = item.dispose()
                    if inspect.isawaitable(res):
                        await res
                elif hasattr(item, "close"):
                    res = item.close()
                    if inspect.isawaitable(res):
                        await res
            except Exception:
                pass
        self._instances.clear()
        self._disposables.clear()

    async def __aenter__(self) -> RequestScope:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.dispose()


ServiceScope = RequestScope
