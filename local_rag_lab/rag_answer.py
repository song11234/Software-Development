from retriever import retrieve


def build_context(chunks: list[dict]) -> str:
    """把召回片段整理成带来源标识的上下文。"""
    lines = []
    for chunk in chunks:
        lines.append(f"[{chunk['id']}|{chunk['source']}] {chunk['text']}")
    return "\n".join(lines)


def answer_with_context(question: str) -> dict:
    """基于检索上下文生成规则化回答，并在无依据时拒答。"""
    chunks = retrieve(question, top_k=3)
    if not chunks:
        return {
            "answer": "资料中没有找到足够依据，无法回答该问题。",
            "sources": [],
            "grounded": False,
        }

    context = build_context(chunks)
    answer = f"根据资料：\n{context}\n\n针对问题「{question}」，可依据上述资料作答。"
    return {
        "answer": answer,
        "sources": [chunk["id"] for chunk in chunks],
        "grounded": True,
    }
