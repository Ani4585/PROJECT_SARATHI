"""
Dynamic Fallback Router for Models and Drivers.
"""
from typing import List, Callable, Awaitable, Any, Optional

class ModelFallbackRouter:
    def __init__(self, primary_driver: Callable[[str], Awaitable[Any]], fallback_drivers: Optional[List[Callable[[str], Awaitable[Any]]]] = None):
        self.primary_driver = primary_driver
        self.fallback_drivers = fallback_drivers or []

    async def execute_with_fallback(self, prompt: str) -> Any:
        drivers = [self.primary_driver] + self.fallback_drivers
        last_error = None

        for idx, driver in enumerate(drivers):
            try:
                result = await driver(prompt)
                return {"result": result, "driver_index": idx, "used_fallback": idx > 0}
            except Exception as e:
                last_error = e

        raise RuntimeError(f"All model drivers failed. Primary and {len(self.fallback_drivers)} fallbacks exhausted. Last error: {last_error}")
