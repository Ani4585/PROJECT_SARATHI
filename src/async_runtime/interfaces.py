class IAsyncInitializer:
    async def initialize_async(self) -> None:
        pass

class IAsyncDisposable:
    async def dispose_async(self) -> None:
        pass
