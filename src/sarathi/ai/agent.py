import inspect
from typing import Dict, Any, Callable, Optional
from .models import ToolSpec, tool

class AIAgent:
    def __init__(self, agent_name: str = "SarathiAIAgent"):
        self.agent_name = agent_name
        self.tools: Dict[str, ToolSpec] = {}

    def bind_tool(self, fn: Callable):
        if hasattr(fn, "_tool_spec"):
            spec = fn._tool_spec
            self.tools[spec.name] = spec
        else:
            spec = tool()(fn)._tool_spec
            self.tools[spec.name] = spec

    async def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not bound to agent '{self.agent_name}'")
        spec = self.tools[tool_name]
        fn = spec.func
        if inspect.iscoroutinefunction(fn):
            return await fn(**arguments)
        return fn(**arguments)
