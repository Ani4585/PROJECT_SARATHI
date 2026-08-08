"""Distributed Workflow State Machine."""
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ROLLED_BACK = "ROLLED_BACK"

class WorkflowState:
    def __init__(self, workflow_id: str, status: WorkflowStatus = WorkflowStatus.PENDING):
        self.workflow_id = workflow_id
        self.status = status
        self.context: Dict[str, Any] = {}
        self.completed_nodes: List[str] = []
        self.failed_nodes: List[str] = []
        self.history: List[Dict[str, Any]] = []
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {"workflow_id": self.workflow_id, "status": self.status.value, "context": self.context, "completed_nodes": self.completed_nodes, "failed_nodes": self.failed_nodes, "history": self.history}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        s = cls(workflow_id=data["workflow_id"], status=WorkflowStatus(data["status"]))
        s.context = data.get("context", {})
        s.completed_nodes = data.get("completed_nodes", [])
        s.failed_nodes = data.get("failed_nodes", [])
        s.history = data.get("history", [])
        return s

class WorkflowStateMachine:
    VALID_TRANSITIONS = {
        WorkflowStatus.PENDING: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
        WorkflowStatus.RUNNING: {WorkflowStatus.PAUSED, WorkflowStatus.WAITING, WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED, WorkflowStatus.ROLLED_BACK},
        WorkflowStatus.PAUSED: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
        WorkflowStatus.WAITING: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
        WorkflowStatus.COMPLETED: set(),
        WorkflowStatus.FAILED: {WorkflowStatus.ROLLED_BACK, WorkflowStatus.RUNNING},
        WorkflowStatus.CANCELLED: set(),
        WorkflowStatus.ROLLED_BACK: set(),
    }

    def __init__(self, state: WorkflowState):
        self.state = state

    def transition_to(self, new_status: WorkflowStatus, reason: Optional[str] = None):
        allowed = self.VALID_TRANSITIONS.get(self.state.status, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid transition from {self.state.status.value} to {new_status.value}")
        old_status = self.state.status
        self.state.status = new_status
        self.state.history.append({"from": old_status.value, "to": new_status.value, "reason": reason or ""})
