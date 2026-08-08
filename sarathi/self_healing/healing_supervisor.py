"""
Self-Healing Supervisor and Recovery Engine.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from sarathi.self_healing.circuit_breaker import AICircuitBreaker

class SelfHealingEngine:
    def __init__(self):
        self.circuit_breakers: Dict[str, AICircuitBreaker] = {}
        self.healing_logs: list = []

    def get_circuit_breaker(self, resource_id: str) -> AICircuitBreaker:
        if resource_id not in self.circuit_breakers:
            self.circuit_breakers[resource_id] = AICircuitBreaker()
        return self.circuit_breakers[resource_id]

    async def execute_healable_task(
        self,
        task_id: str,
        primary_fn: Callable[[], Awaitable[Any]],
        recovery_fn: Optional[Callable[[], Awaitable[Any]]] = None
    ) -> Dict[str, Any]:
        cb = self.get_circuit_breaker(task_id)

        try:
            res = await cb.call(primary_fn)
            return {"status": "SUCCESS", "result": res, "healed": False}
        except Exception as primary_error:
            self.healing_logs.append({"task_id": task_id, "primary_error": str(primary_error), "action": "ATTEMPTING_RECOVERY"})

            if recovery_fn:
                try:
                    healed_res = await recovery_fn()
                    self.healing_logs.append({"task_id": task_id, "action": "RECOVERY_SUCCESS"})
                    return {"status": "SUCCESS", "result": healed_res, "healed": True, "error": str(primary_error)}
                except Exception as recovery_error:
                    self.healing_logs.append({"task_id": task_id, "recovery_error": str(recovery_error), "action": "RECOVERY_FAILED"})
                    raise recovery_error
            else:
                raise primary_error
