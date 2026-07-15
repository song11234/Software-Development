import json
from pathlib import Path

from agents import checkpoint_agent, planner_agent, programmer_agent, reviewer_agent, tester_agent
from state import GoalContract, WorkflowState


def write_history(state: WorkflowState, path: str | Path) -> None:
    """保存状态转移历史，便于报告分析和故障复盘。"""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(state.history, ensure_ascii=False, indent=2), encoding="utf-8")


def run_workflow(
    goal: GoalContract,
    auto_approve: bool = True,
    log_path: str | Path | None = None,
    max_attempts: int = 3,
) -> WorkflowState:
    """执行多 Agent 状态机，直到成功、失败或等待人工确认。"""

    state = WorkflowState(goal=goal, max_attempts=max_attempts)
    state.log("start", goal.objective)

    state = planner_agent(state)

    while state.attempts < state.max_attempts:
        state = programmer_agent(state)
        state = reviewer_agent(state)

        if not state.review_passed:
            state.log("router", "审查未通过，返回 Programmer")
            continue

        state = tester_agent(state)
        if not state.tests_passed:
            state.log("router", "测试未通过，返回 Programmer")
            continue

        state = checkpoint_agent(state, auto_approve=auto_approve)
        if log_path is not None:
            write_history(state, log_path)
        return state

    state.status = "failed"
    state.log("router", "达到最大尝试次数，工作流失败")
    if log_path is not None:
        write_history(state, log_path)
    return state
