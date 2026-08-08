import json
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple

@dataclass
class GatewayRequest:
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None

@dataclass
class GatewayResponse:
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None

    def json(self, data: Any, status_code: int = 200):
        self.status_code = status_code
        self.headers["Content-Type"] = "application/json"
        self.body = json.dumps(data)
        return self

class GatewayContext:
    def __init__(self, request: GatewayRequest):
        self.request = request
        self.response = GatewayResponse()
        self.state: Dict[str, Any] = {}
        self.start_time = time.monotonic()

class GatewayRoute:
    def __init__(self, path_pattern: str, methods: List[str], handler: Callable, name: str = ""):
        self.path_pattern = path_pattern
        self.methods = [m.upper() for m in methods]
        self.handler = handler
        self.name = name or handler.__name__
        self._regex, self._param_names = self._compile_pattern(path_pattern)

    def _compile_pattern(self, pattern: str) -> Tuple[re.Pattern, List[str]]:
        param_names = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', pattern)
        regex_pattern = '^' + re.sub(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', r'([^/]+)', pattern) + '$'
        return re.compile(regex_pattern), param_names

    def match(self, path: str, method: str) -> Optional[Dict[str, str]]:
        if method.upper() not in self.methods and "*" not in self.methods:
            return None
        m = self._regex.match(path)
        if not m:
            return None
        return dict(zip(self._param_names, m.groups()))
