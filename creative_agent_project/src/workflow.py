"""AI 资料整理工作流 —— 分类、打标签、摘要、要点提取。

对应知识点：
- 第02章：AI Agent 工具调用（openai SDK）
- 第06章：提示词工程（结构化 prompt，要求 JSON 输出）
- 第07章：Harness 安全护栏（token budget 检查）
- 第08章：Token 成本追踪
- 第09章：多步骤工作流编排
"""
import json
from openai import OpenAI
from src.config import get_config


# ── 提示词模板（第06章：提示词工程） ──

ORGANIZE_SYSTEM_PROMPT = """你是一个专业的资料整理助手。你的任务是对用户提交的文档进行分析整理。

你必须严格以 JSON 格式返回结果，不要包含任何其他文字。

JSON 结构：
{
    "category": "类别名称",
    "tags": ["标签1", "标签2", "标签3"],
    "summary": "2-3句话的摘要，不超过150字",
    "key_points": ["要点1", "要点2", "要点3", "要点4"]
}

分类体系（选择最合适的一个）：
- 技术/编程
- 学术/研究
- 工作/管理
- 学习/笔记
- 创意/设计
- 生活/其他

标签要求：3-5个精准的关键词，体现文档核心主题。
摘要要求：概括文档的核心内容和结论，避免评价性语言。
要点要求：3-5个独立的关键信息点，每条不超过50字。"""


# ── 工作流函数 ──

def organize_document(title: str, content: str) -> dict:
    """对单篇文档执行 AI 整理：分类、标签、摘要、要点提取。

    对应知识点：
    - 第02章 MCP 工具调用模式
    - 第06章 提示词工程中的结构化输出
    - 第07章 Token budget 控制（max_tokens 参数）
    - 第08章 Token 成本追踪（返回 usage 信息）
    """
    config = get_config()
    if not config.is_api_key_valid():
        raise RuntimeError(
            "未配置有效的 OPENAI_API_KEY。请在 .env 文件中设置。"
        )
    client = OpenAI(api_key=config.openai_api_key, base_url=config.openai_base_url)

    # 截断过长内容（第07章：token budget）
    content_snippet = content[:config.max_tokens_per_request]

    response = client.chat.completions.create(
        model=config.model_name,
        messages=[
            {"role": "system", "content": ORGANIZE_SYSTEM_PROMPT},
            {"role": "user", "content": f"文档标题：{title}\n\n文档内容：\n{content_snippet}"},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    raw_text = response.choices[0].message.content.strip()

    # 清理可能的 markdown 代码块包裹
    result = _parse_json_response(raw_text)

    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        "total_tokens": response.usage.total_tokens if response.usage else 0,
    }

    return {"result": result, "token_usage": usage}


def _parse_json_response(raw: str) -> dict:
    """从 AI 响应中提取 JSON —— 处理 markdown 代码块包裹。

    对应知识点：第06章提示词工程 —— 结构化输出的鲁棒解析。
    """
    text = raw.strip()
    # 移除 markdown 代码块标记
    for prefix in ["```json", "```"]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return json.loads(text)
