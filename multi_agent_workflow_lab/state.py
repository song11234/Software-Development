from dataclasses import dataclass, field
from typing import Literal


WorkflowStatus = Literal["created", "planning", "coding", "reviewing", "testing", "waiting_for_human", "done", "failed"]


@dataclass
class GoalContract:
    """目标契约说明本轮 Agent 工作到底要完成什么。"""

    objective: str
    success_criteria: list[str]
    constraints: list[str]
    stop_conditions: list[str]


@dataclass
class WorkflowState:
    """多 Agent 共享状态，调度器只根据这个对象决定下一步。"""

    goal: GoalContract
    status: WorkflowStatus = "created"
    plan: list[str] = field(default_factory=list)
    draft: str = ""
    review_passed: bool = False
    review_feedback: str = ""
    tests_passed: bool = False
    checkpoint_required: bool = False
    human_approved: bool = False
    attempts: int = 0
    max_attempts: int = 3
    history: list[dict] = field(default_factory=list)

    def log(self, node: str, message: str) -> None:
        """记录每一步状态变化，便于审计和复盘。"""

        self.history.append({
            "step": len(self.history) + 1,
            "node": node,
            "status": self.status,
            "message": message,
        })
