from collections import defaultdict

from vector_db import is_expired, search_vector_db
from student_info import print_student_id


def format_citation(chunk: dict) -> dict:
    """把检索片段转换为回答中可展示的引用来源。"""
    metadata = chunk["metadata"]
    return {
        "chunk_id": chunk["chunk_id"],
        "title": metadata["title"],
        "source": metadata["source"],
        "updated_at": metadata["updated_at"],
        "expires_at": metadata["expires_at"],
        "score": chunk["score"],
        "expired": chunk["expired"],
    }


def detect_conflicts(chunks: list[dict]) -> dict:
    """识别同一 claim_key 下是否存在多个不同 claim_value。"""
    grouped = defaultdict(lambda: defaultdict(list))
    for chunk in chunks:
        metadata = chunk["metadata"]
        key = metadata.get("claim_key")
        value = metadata.get("claim_value")
        if key and value:
            grouped[key][value].append(chunk["chunk_id"])

    conflicts = {}
    for key, values in grouped.items():
        if len(values) > 1:
            conflicts[key] = dict(values)
    return conflicts


def build_evidence_lines(chunks: list[dict]) -> list[str]:
    """把多个资料片段整理成可直接展示的证据行。"""
    lines = []
    for chunk in chunks:
        meta = chunk["metadata"]
        status = "已过期" if is_expired(meta) else "有效"
        lines.append(
            f"- {chunk['text']} "
            f"[{chunk['chunk_id']}；{meta['title']}；{status}；score={chunk['score']}]"
        )
    return lines


def synthesize_answer(question: str, chunks: list[dict], warnings: list[str]) -> str:
    """在不调用模型的情况下，生成带证据和告警的规则化回答。"""
    evidence = "\n".join(build_evidence_lines(chunks))
    warning_text = ""
    if warnings:
        warning_text = "注意：" + "；".join(warnings) + "\n"

    return (
        f"问题：{question}\n"
        f"{warning_text}"
        "根据当前可访问资料，可以综合如下：\n"
        f"{evidence}\n"
        "以上回答只基于列出的引用来源。"
    )


def answer_with_governance(
    question: str,
    role: str = "student",
    include_expired: bool = False,
) -> dict:
    """执行检索治理流程，返回回答、引用、告警和 grounded 状态。"""
    chunks = search_vector_db(
        question=question,
        role=role,
        top_k=5,
        include_expired=include_expired,
    )

    if not chunks:
        return {
            "answer": "资料中没有找到足够依据，无法回答该问题。",
            "citations": [],
            "warnings": [],
            "grounded": False,
        }

    warnings = []
    expired_chunks = [chunk for chunk in chunks if chunk["expired"]]
    if expired_chunks:
        warnings.append(
            "检索结果包含过期资料，请优先参考未过期来源，并在实验记录中说明处理方式。"
        )

    conflicts = detect_conflicts(chunks)
    if conflicts:
        warnings.append(
            f"检测到同一主题存在冲突内容：{conflicts}。回答时应提示用户需要人工确认。"
        )

    return {
        "answer": synthesize_answer(question, chunks, warnings),
        "citations": [format_citation(chunk) for chunk in chunks],
        "warnings": warnings,
        "grounded": True,
    }
