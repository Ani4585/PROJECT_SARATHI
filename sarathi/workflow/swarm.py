from enum import Enum
from typing import List, Dict, Any, Callable, Awaitable
class SwarmRole(str, Enum): WORKER="WORKER"; CRITIC="CRITIC"
class SwarmAgent:
    def __init__(self, agent_id, role, handler): self.agent_id, self.role, self.handler = agent_id, role, handler
class AgentSwarmOrchestrator:
    def __init__(self, agents): self.agents = {a.agent_id: a for a in agents}
    async def execute_critic_consensus(self, worker_id, critic_id, prompt):
        w = await self.agents[worker_id].handler(prompt, {})
        c = await self.agents[critic_id].handler(f"Critique: {w}", {})
        return w
