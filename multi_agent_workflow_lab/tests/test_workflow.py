from state import GoalContract
from workflow import run_workflow


def make_goal() -> GoalContract:
    return GoalContract(
        objective="实现 add(a, b)",
        success_criteria=["add(2, 3) == 5"],
        constraints=["不访问文件系统", "不调用网络"],
        stop_conditions=["测试通过", "达到最大尝试次数"],
    )


def test_workflow_success_path(tmp_path):
    state = run_workflow(make_goal(), auto_approve=True, log_path=tmp_path / "history.json")

    assert state.status == "done"
    assert state.tests_passed is True
    assert state.human_approved is True
    assert state.attempts == 2
    assert any(item["node"] == "reviewer" and "减法" in item["message"] for item in state.history)
    assert (tmp_path / "history.json").exists()


def test_workflow_can_wait_for_human():
    state = run_workflow(make_goal(), auto_approve=False)

    assert state.status == "waiting_for_human"
    assert state.checkpoint_required is True
    assert state.human_approved is False


def test_workflow_has_failure_exit():
    state = run_workflow(make_goal(), auto_approve=True, max_attempts=1)

    assert state.status == "failed"
    assert state.attempts == 1
