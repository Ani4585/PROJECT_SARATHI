"""
Workflow Execution Interceptors and Hooks.
"""
from typing import Dict, Any, Optional

class BaseWorkflowInterceptor:
    async def on_node_start(self, node_id: str, context: Dict[str, Any]):
        pass

    async def on_node_success(self, node_id: str, result: Any, context: Dict[str, Any]):
        pass

    async def on_node_failure(self, node_id: str, error: Exception, context: Dict[str, Any]):
        pass

class LoggingWorkflowInterceptor(BaseWorkflowInterceptor):
    def __init__(self):
        self.events = []

    async def on_node_start(self, node_id: str, context: Dict[str, Any]):
        self.events.append(f"START:{node_id}")

    async def on_node_success(self, node_id: str, result: Any, context: Dict[str, Any]):
        self.events.append(f"SUCCESS:{node_id}")

    async def on_node_failure(self, node_id: str, error: Exception, context: Dict[str, Any]):
        self.events.append(f"FAILURE:{node_id}")
