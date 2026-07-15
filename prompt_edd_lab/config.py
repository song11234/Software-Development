"""
DeepSeek 模型适配器 — OpenAI 兼容接口
用法: from config import get_llm_response
"""

import os
from openai import OpenAI

# 从 .env 加载配置
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

_load_env()

_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)


def get_llm_response(
    prompt: str,
    system: str = "你是一个有用的AI助手。",
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """调用 DeepSeek 获取回复"""
    model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    resp = _client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


def verify_connection() -> dict:
    """验证 DeepSeek 连接是否正常"""
    try:
        reply = get_llm_response(
            "请用一句话说明什么是评估驱动开发。",
            max_tokens=100,
        )
        return {"ok": True, "reply": reply.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    result = verify_connection()
    if result["ok"]:
        print("[OK] DeepSeek connected successfully")
        print(f"Reply: {result['reply']}")
    else:
        print(f"[FAIL] Connection error: {result['error']}")
