from state import GoalContract
from workflow import run_workflow

goal = GoalContract(
    objective="实现 add(a, b)，返回两数和",
    success_criteria=["add(2,3)==5"],
    constraints=["不访问文件系统"],
    stop_conditions=["测试通过"],
)

state = run_workflow(goal, auto_approve=True, log_path="outputs/history.json")
print("status:", state.status)
print("attempts:", state.attempts)
print("tests_passed:", state.tests_passed)
print("human_approved:", state.human_approved)
print("history steps:", len(state.history))
print("OK")
