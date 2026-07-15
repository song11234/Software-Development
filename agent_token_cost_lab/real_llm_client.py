import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


class LlmError(RuntimeError):
    """把 HTTP、网络和响应格式错误统一成实验可解释的异常。"""


@dataclass
class Usage:
    """记录一次模型调用的 Token 用量。estimated 表示是否来自本地估算。"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated: bool


@dataclass
class LlmResponse:
    """真实模型调用的最小返回结构，供运行时控制器和实验脚本复用。"""

    content: str
    model: str
    usage: Usage
    elapsed_ms: int


def load_env_file(path: str = ".env") -> None:
    """读取简单 .env 文件；已存在的环境变量优先级更高。"""

    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_env(name: str, default: str | None = None, *, required: bool = False) -> str:
    """集中读取环境变量，缺少必填配置时给出明确错误。"""

    value = os.getenv(name, default)
    if required and not value:
        raise LlmError(f"missing environment variable: {name}")
    return value or ""


def estimate_tokens(text: str) -> int:
    """教学用 Token 估算：中文约 1 字 1 token，英文约 4 字符 1 token。"""

    if not text:
        return 0
    chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    other_chars = len(text) - chinese_chars
    return chinese_chars + max(1, other_chars // 4)


def estimate_messages_tokens(messages: list[dict]) -> int:
    """估算 Chat Completions messages 的输入 Token，包含少量协议开销。"""

    total = 2
    for message in messages:
        total += 4
        total += estimate_tokens(str(message.get("role", "")))
        total += estimate_tokens(str(message.get("content", "")))
    return max(1, total)


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """根据 .env 中的千 Token 单价估算费用，本地模型可把单价设为 0。"""

    input_price = float(get_env("LLM_PRICE_INPUT_PER_1K", "0"))
    output_price = float(get_env("LLM_PRICE_OUTPUT_PER_1K", "0"))
    cost = prompt_tokens / 1000 * input_price + completion_tokens / 1000 * output_price
    return round(cost, 6)


def build_chat_endpoint(base_url: str) -> str:
    """把 /v1 基础地址转换成 chat/completions 完整端点。"""

    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def chat_completion(messages: list[dict], *, timeout: float | None = None) -> LlmResponse:
    """调用真实 OpenAI-compatible 模型，并返回内容、usage 和耗时。"""

    load_env_file()
    base_url = get_env("LLM_BASE_URL", required=True)
    api_key = get_env("LLM_API_KEY", required=True)
    model = get_env("LLM_MODEL", required=True)
    max_tokens = int(get_env("LLM_MAX_OUTPUT_TOKENS", "96"))
    request_timeout = timeout or float(get_env("LLM_TIMEOUT_SECONDS", "60"))

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "stream": False,
    }
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    request = urllib.request.Request(
        build_chat_endpoint(base_url),
        data=data,
        headers=headers,
        method="POST",
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=request_timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")[:300]
        raise LlmError(f"http_{exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise LlmError(f"network_error: {exc.reason}") from exc

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError("invalid_chat_completion_response") from exc

    usage_payload = payload.get("usage") or {}
    if "prompt_tokens" in usage_payload and "completion_tokens" in usage_payload:
        usage = Usage(
            prompt_tokens=int(usage_payload["prompt_tokens"]),
            completion_tokens=int(usage_payload["completion_tokens"]),
            total_tokens=int(usage_payload.get("total_tokens", 0))
            or int(usage_payload["prompt_tokens"]) + int(usage_payload["completion_tokens"]),
            estimated=False,
        )
    else:
        prompt_tokens = estimate_messages_tokens(messages)
        completion_tokens = estimate_tokens(content)
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated=True,
        )

    return LlmResponse(
        content=content,
        model=str(payload.get("model") or model),
        usage=usage,
        elapsed_ms=elapsed_ms,
    )
