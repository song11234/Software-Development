import json

from state import GoalContract
from workflow import run_workflow


goal = GoalContract(
    objective="实现一个 add(a, b) 函数，返回两个数字之和。",
    success_criteria=["add(2, 3) == 5", "代码中使用加法而不是减法"],
    constraints=["不访问文件系统", "不调用网络", "最多尝试 3 次"],
    stop_conditions=["测试通过并经过检查点", "达到最大尝试次数"],
)

state = run_workflow(goal, auto_approve=True, log_path="outputs/history.json")

print("status:", state.status)
print("attempts:", state.attempts)
print("tests_passed:", state.tests_passed)
print("human_approved:", state.human_approved)
print("=" * 80)
print(json.dumps(state.history, ensure_ascii=False, indent=2))
