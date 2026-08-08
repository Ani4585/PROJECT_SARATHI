"""Milestone 55 Tests."""
import asyncio
from sarathi.workflow import TaskNode, TaskDAG, DAGExecutor, DAGCycleError, WorkflowManager, SwarmAgent, SwarmRole, AgentSwarmOrchestrator

def test_dag_topological_sort():
    dag = TaskDAG()
    async def h(ctx): return 1
    dag.add_node(TaskNode("n1", h))
    dag.add_node(TaskNode("n2", h, dependencies={"n1"}))
    assert len(dag.get_topological_order()) == 2

def test_workflow_manager_e2e():
    async def run():
        mgr = WorkflowManager()
        dag = TaskDAG()
        async def h1(ctx): return ctx.get("in", 0) + 10
        dag.add_node(TaskNode("s1", h1))
        mgr.register_dag("d1", dag)
        res = await mgr.execute_dag_workflow("d1", "wf1", {"in": 5})
        assert res["node_outputs"]["s1"] == 15
    asyncio.run(run())
