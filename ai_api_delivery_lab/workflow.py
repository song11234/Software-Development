def run_ai_workflow(question: str) -> dict:
    """教学用 AI 工作流：根据问题返回结构化答案。"""

    question = question.strip()
    if not question:
        return {
            "answer": "问题不能为空。",
            "sources": [],
            "ok": False,
        }

    if "RAG" in question or "检索" in question:
        answer = "RAG 通过检索外部资料增强回答，可以降低幻觉风险。"
        sources = ["course_notes:rag"]
    elif "Harness" in question or "护栏" in question:
        answer = "Harness 工程通过代码级护栏限制 Agent 的工具调用范围。"
        sources = ["course_notes:harness"]
    elif "Agent" in question or "状态机" in question:
        answer = "Agent 工作流可以用目标契约、状态机、检查点和测试结果来约束。"
        sources = ["course_notes:agent_workflow"]
    else:
        answer = "当前示例工作流没有找到足够资料，可在后续接入真实 RAG。"
        sources = []

    return {
        "answer": answer,
        "sources": sources,
        "ok": bool(sources),
    }
