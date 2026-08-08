"""Workflow State Machine."""
from enum import Enum
from typing import Dict, Any, List

class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class WorkflowState:
    def __init__(self, workflow_id: str, status: WorkflowStatus = WorkflowStatus.PENDING):
        self.workflow_id, self.status, self.context, self.completed_nodes = workflow_id, status, {}, []
    def to_dict(self): return {"workflow_id": self.workflow_id, "status": self.status.value, "context": self.context, "completed_nodes": self.completed_nodes}

class WorkflowStateMachine:
    def __init__(self, state: WorkflowState): self.state = state
    def transition_to(self, new_status: WorkflowStatus): self.state.status = new_status
