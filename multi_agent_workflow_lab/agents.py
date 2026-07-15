from state import WorkflowState


def planner_agent(state: WorkflowState) -> WorkflowState:
    """Planner 将目标拆成可检查的执行步骤。"""

    state.status = "planning"
    state.plan = [
        "实现 add(a, b) 函数",
        "审查函数是否真正执行加法",
        "运行最小测试 add(2, 3) == 5",
        "通过检查点后结束工作流",
    ]
    state.log("planner", "形成四步执行计划")
    return state


def programmer_agent(state: WorkflowState) -> WorkflowState:
    """Programmer 根据反馈生成候选代码。"""

    state.status = "coding"
    state.attempts += 1
    if state.attempts == 1:
        state.draft = "def add(a, b):\n    return a - b\n"
    else:
        state.draft = "def add(a, b):\n    return a + b\n"
    state.log("programmer", f"生成第 {state.attempts} 版代码")
    return state


def reviewer_agent(state: WorkflowState) -> WorkflowState:
    """Reviewer 只给反馈，不直接修改 Programmer 的代码。"""

    state.status = "reviewing"
    if "return a + b" in state.draft:
        state.review_passed = True
        state.review_feedback = "代码逻辑符合加法需求。"
    else:
        state.review_passed = False
        state.review_feedback = "当前代码使用了减法，不符合 add 函数需求。"
    state.log("reviewer", state.review_feedback)
    return state


def tester_agent(state: WorkflowState) -> WorkflowState:
    """Tester 执行受控教学代码，验证结果是否符合成功标准。"""

    state.status = "testing"
    namespace: dict = {"__builtins__": {}}
    try:
        exec(state.draft, namespace)
        result = namespace["add"](2, 3)
        state.tests_passed = result == 5
        message = "测试通过" if state.tests_passed else f"测试失败：add(2, 3)={result}"
    except Exception as exc:
        state.tests_passed = False
        message = f"测试异常：{type(exc).__name__}"
    state.log("tester", message)
    return state


def checkpoint_agent(state: WorkflowState, auto_approve: bool) -> WorkflowState:
    """Checkpoint 模拟人工确认；真实项目中这里可能暂停等待用户。"""

    state.checkpoint_required = True
    if auto_approve:
        state.human_approved = True
        state.status = "done"
        state.log("checkpoint", "检查点自动批准，工作流结束")
    else:
        state.human_approved = False
        state.status = "waiting_for_human"
        state.log("checkpoint", "等待人工确认")
    return state
