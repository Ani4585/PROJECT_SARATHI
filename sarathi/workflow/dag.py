"""Task DAG Engine."""
import asyncio
from typing import List, Dict, Any, Optional, Set, Callable, Awaitable
from collections import defaultdict, deque

class DAGCycleError(Exception): pass

class TaskNode:
    def __init__(self, node_id: str, handler: Callable[[Dict[str, Any]], Awaitable[Any]], dependencies: Optional[Set[str]] = None):
        self.node_id, self.handler, self.dependencies = node_id, handler, dependencies or set()

class TaskDAG:
    def __init__(self): self.nodes: Dict[str, TaskNode] = {}
    def add_node(self, node: TaskNode): self.nodes[node.node_id] = node
    def validate(self):
        in_deg = {nid: 0 for nid in self.nodes}
        adj = defaultdict(set)
        for nid, node in self.nodes.items():
            for dep in node.dependencies:
                adj[dep].add(nid)
                in_deg[nid] += 1
        queue = deque([nid for nid, deg in in_deg.items() if deg == 0])
        visited = 0
        while queue:
            curr = queue.popleft()
            visited += 1
            for nxt in adj[curr]:
                in_deg[nxt] -= 1
                if in_deg[nxt] == 0: queue.append(nxt)
        if visited != len(self.nodes): raise DAGCycleError("Cycle detected in DAG.")

    def get_topological_order(self) -> List[str]:
        self.validate()
        return list(self.nodes.keys())

class DAGExecutor:
    def __init__(self, dag: TaskDAG): self.dag = dag; self.dag.validate()
    async def execute(self, initial_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = (initial_inputs or {}).copy()
        node_results, completed = {}, set()
        in_deg = {nid: 0 for nid in self.dag.nodes}
        adj = defaultdict(set)
        for nid, node in self.dag.nodes.items():
            for dep in node.dependencies:
                adj[dep].add(nid)
                in_deg[nid] += 1

        while len(completed) < len(self.dag.nodes):
            ready = [nid for nid, deg in in_deg.items() if deg == 0 and nid not in completed]
            if not ready: raise RuntimeError("Deadlock in DAG.")
            tasks = [self.dag.nodes[nid].handler(context) for nid in ready]
            results = await asyncio.gather(*tasks)
            for nid, res in zip(ready, results):
                completed.add(nid)
                node_results[nid] = res
                context[f"node_{nid}_output"] = res
                for nxt in adj[nid]: in_deg[nxt] -= 1
        return {"node_outputs": node_results, "context": context}
