import inspect
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable

@dataclass
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = "call_default"

def tool(name: Optional[str] = None, description: str = ""):
    def decorator(fn: Callable):
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__.strip() if fn.__doc__ else "No description")

        sig = inspect.signature(fn)
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            properties[param_name] = {"type": param_type}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        params_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        spec = ToolSpec(name=tool_name, description=tool_desc, parameters=params_schema, func=fn)
        fn._tool_spec = spec
        return fn
    return decorator
