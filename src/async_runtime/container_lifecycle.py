import asyncio
from typing import Any, List
from .interfaces import IAsyncInitializer, IAsyncDisposable

class AsyncContainerLifecycleManager:
    def __init__(self) -> None:
        self._managed_instances: List[Any] = []

    def register_instance(self, instance: Any) -> Any:
        if instance not in self._managed_instances:
            self._managed_instances.append(instance)
        return instance

    async def initialize_all(self) -> None:
        for inst in list(self._managed_instances):
            if isinstance(inst, IAsyncInitializer) or hasattr(inst, "initialize_async"):
                init_fn = getattr(inst, "initialize_async", None)
                if callable(init_fn):
                    await init_fn()

    async def dispose_all(self) -> None:
        for inst in reversed(list(self._managed_instances)):
            if isinstance(inst, IAsyncDisposable) or hasattr(inst, "dispose_async"):
                dispose_fn = getattr(inst, "dispose_async", None)
                if callable(dispose_fn):
                    await dispose_fn()
        self._managed_instances.clear()

    async def __aenter__(self) -> "AsyncContainerLifecycleManager":
        await self.initialize_all()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.dispose_all()
