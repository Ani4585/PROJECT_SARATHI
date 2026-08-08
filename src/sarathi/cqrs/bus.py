import inspect
from typing import Dict, Type, Callable, Any

class CommandBus:
    def __init__(self):
        self._handlers: Dict[Type, Callable] = {}

    def register(self, command_type: Type, handler: Callable):
        self._handlers[command_type] = handler

    async def dispatch(self, command: Any) -> Any:
        cmd_type = type(command)
        if cmd_type not in self._handlers:
            raise KeyError(f"No handler registered for command {cmd_type.__name__}")
        handler = self._handlers[cmd_type]
        if inspect.iscoroutinefunction(handler):
            return await handler(command)
        return handler(command)

class QueryBus(CommandBus):
    """QueryBus for read-side queries without state mutation."""
    pass
