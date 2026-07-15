from state import GoalContract
from workflow import run_workflow


goal = GoalContract(
    objective="实现一个 add(a, b) 函数，返回两个数字之和。",
    success_criteria=["add(2, 3) == 5"],
    constraints=["不访问文件系统", "不调用网络"],
    stop_conditions=["测试通过后等待人工确认", "达到最大尝试次数"],
)

state = run_workflow(goal, auto_approve=False, log_path="outputs/manual_gate_history.json")

print("status:", state.status)
print("checkpoint_required:", state.checkpoint_required)
print("human_approved:", state.human_approved)
