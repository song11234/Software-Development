from chroma_vector_db import build_chroma_store
from llm_rag_answer import answer_with_deepseek

QUESTIONS = [
    "原石、祈愿和角色养成有什么关系？",
    "课堂讲角色养成时有什么建议？",
    "原粹树脂应该优先做什么？",
]


def run_case(question: str, role: str = "student", include_expired: bool = False) -> None:
    """运行一次 DeepSeek RAG 问答，并打印回答、引用和告警。"""
    print("=" * 80)
    print("question:", question)
    print("role:", role)
    try:
        result = answer_with_deepseek(
            question=question,
            role=role,
            include_expired=include_expired,
        )
    except Exception as exc:
        print("deepseek_skipped_or_failed:", exc)
        return

    print(result["answer"])
    print("citations:", result["citations"])
    print("warnings:", result["warnings"])


build_chroma_store()

# Q1: 多文档综合（student 角色，不包含过期资料）
run_case(QUESTIONS[0])

# Q2: 课堂建议，student 角色不应看到教师私密资料
run_case(QUESTIONS[1], role="student")

# Q3: 树脂建议，允许过期资料以触发冲突警告
run_case(QUESTIONS[2], include_expired=True)
