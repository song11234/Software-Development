"""RAG 检索增强生成 —— 基于已整理资料回答问题。

对应知识点：
- 第03章：本地 RAG 与知识增强问答（检索 → 增强 → 生成）
- 第06章：提示词工程（严格控制仅基于资料回答）
- 第07章：安全护栏（拒答机制）
- 第08章：Token 成本控制（限制上下文长度）
"""
from openai import OpenAI
from src.config import get_config
from src.store import DocumentStore


# ── 提示词模板 ──

RAG_PROMPT_TEMPLATE = """你是一个基于资料库的知识问答助手。请严格根据以下资料回答用户问题。

## 规则（第07章安全护栏）：
1. 只基于提供的资料内容回答，不要编造信息
2. 如果资料不足以回答问题，明确回答"资料库中暂无相关信息，无法回答此问题"
3. 引用时注明来源文档标题
4. 回答简洁清晰，不超过300字
5. 如果资料中有矛盾，如实说明

## 相关资料：
{context}

## 用户问题：
{question}

## 回答："""


def answer_question(
    question: str,
    store: DocumentStore,
    category: str | None = None,
    top_k: int = 5,
) -> dict:
    """RAG 问答：检索 → 构建上下文 → LLM 生成回答。

    Args:
        question: 用户问题
        store: 文档存储实例
        category: 限定的资料分类
        top_k: 检索返回的文档数
    """
    # 第03章：Step 1 — 检索
    search_results = store.search(question, category=category, top_k=top_k)

    if not search_results:
        return {
            "ok": True,
            "answer": "资料库中暂无与您问题相关的内容。请尝试更换关键词或先添加相关文档。",
            "sources": [],
            "token_usage": {"total_tokens": 0},
        }

    # 第03章：Step 2 — 构建上下文（控制 token 开销）
    contexts = []
    config = get_config()
    max_content_chars = min(config.max_tokens_per_request * 2, 6000)  # ~2 chars/token

    for i, result in enumerate(search_results[:3]):
        doc = store.get(result["document_id"])
        if doc is None:
            continue
        content_preview = doc.get("content", "")[:800]
        context_block = (
            f"【文档{i + 1}】标题: {doc.get('title', '')}\n"
            f"分类: {doc.get('category', '')}\n"
            f"标签: {', '.join(doc.get('tags', []))}\n"
            f"摘要: {doc.get('summary', '')}\n"
            f"要点: {'; '.join(doc.get('key_points', []))}\n"
            f"内容节选: {content_preview}\n"
        )
        if len("\n---\n".join(contexts)) + len(context_block) > max_content_chars:
            break
        contexts.append(context_block)

    context_text = "\n---\n".join(contexts)

    # 第03章：Step 3 — AI 生成回答
    if not config.is_api_key_valid():
        raise RuntimeError(
            "未配置有效的 OPENAI_API_KEY。请在 .env 文件中设置。"
        )
    client = OpenAI(api_key=config.openai_api_key, base_url=config.openai_base_url)

    prompt = RAG_PROMPT_TEMPLATE.format(context=context_text, question=question)

    response = client.chat.completions.create(
        model=config.model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )

    answer = response.choices[0].message.content.strip()

    # 第07章：拒答检测 —— 如果模型说无法回答，明确标记
    if "无法回答" in answer or "暂无相关" in answer:
        answer = "资料库中暂无相关信息，无法回答此问题。"

    return {
        "ok": True,
        "answer": answer,
        "sources": [
            {
                "document_id": r["document_id"],
                "title": r["title"],
                "relevance_score": r["relevance_score"],
            }
            for r in search_results[:3]
        ],
        "token_usage": {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        },
    }
