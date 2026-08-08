"""Workflow Manager."""
from typing import Dict, Any, Optional
from sarathi.workflow.dag import TaskDAG, DAGExecutor
from sarathi.workflow.state_machine import WorkflowState, WorkflowStateMachine, WorkflowStatus

class WorkflowManager:
    def __init__(self): self.dags: Dict[str, TaskDAG] = {}; self.states: Dict[str, WorkflowState] = {}
    def register_dag(self, dag_id: str, dag: TaskDAG): dag.validate(); self.dags[dag_id] = dag
    def create_workflow_state(self, workflow_id: str) -> WorkflowState:
        s = WorkflowState(workflow_id=workflow_id)
        self.states[workflow_id] = s
        return s
    async def execute_dag_workflow(self, dag_id: str, workflow_id: str, initial_inputs: Optional[Dict[str, Any]] = None):
        dag = self.dags[dag_id]
        state = self.states.get(workflow_id) or self.create_workflow_state(workflow_id)
        sm = WorkflowStateMachine(state)
        sm.transition_to(WorkflowStatus.RUNNING)
        res = await DAGExecutor(dag).execute(initial_inputs)
        state.context.update(res["context"])
        state.completed_nodes = list(res["node_outputs"].keys())
        sm.transition_to(WorkflowStatus.COMPLETED)
        return res
