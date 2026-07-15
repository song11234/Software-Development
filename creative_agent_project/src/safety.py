"""安全护栏 —— 频率限制、Token 预算、内容过滤。

对应知识点：
- 第07章 Harness 工程与 Agent 安全护栏
- 第08章 Token 成本控制（budget 检查）
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ── 频率限制器（第07章） ──

class RateLimiter:
    """滑动窗口频率限制。

    核心设计：
    - 基于客户端 IP/ID 分别计数
    - 60 秒滑动窗口
    - 到达上限后返回 429
    """

    def __init__(self, max_per_minute: int = 20):
        self.max_per_minute = max_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, client_id: str = "default") -> tuple[bool, str]:
        now = time.time()
        window_start = now - 60
        self._windows[client_id] = [
            t for t in self._windows[client_id] if t > window_start
        ]
        current = len(self._windows[client_id])
        if current >= self.max_per_minute:
            return False, f"请求频率超限：{self.max_per_minute} 次/分钟，请稍后再试"
        self._windows[client_id].append(now)
        return True, "ok"

    def remaining(self, client_id: str = "default") -> int:
        """剩余可用请求数。"""
        now = time.time()
        window_start = now - 60
        self._windows[client_id] = [
            t for t in self._windows[client_id] if t > window_start
        ]
        return max(0, self.max_per_minute - len(self._windows[client_id]))


# ── Token 预算检查（第08章） ──

class TokenBudget:
    """Token 用量预算控制。

    每次 LLM 调用前检查预估 token 数是否超出预算。
    """

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self._used: dict[str, int] = defaultdict(int)

    def check(self, request_id: str, estimated: int) -> tuple[bool, str]:
        if estimated > self.max_tokens:
            return False, f"预估 Token 用量 ({estimated}) 超过单次预算 ({self.max_tokens})"
        return True, "ok"

    def record(self, request_id: str, actual: int) -> None:
        self._used[request_id] += actual

    def get_usage(self, request_id: str) -> int:
        return self._used.get(request_id, 0)


# ── 内容安全过滤（第07章） ──

class ContentFilter:
    """内容安全过滤器。

    检查用户输入和 AI 输出中是否包含不当内容。
    实际生产环境可接入更完整的安全审核服务。
    """

    # 敏感词列表（示例，实际应由安全团队维护）
    BLOCKED_PATTERNS: list[str] = []

    @classmethod
    def check_input(cls, text: str) -> tuple[bool, Optional[str]]:
        """检查用户输入内容。"""
        if not text or not text.strip():
            return False, "输入内容不能为空"
        text_lower = text.lower()
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern.lower() in text_lower:
                return False, "输入内容包含不合规信息，请修改后重试"
        return True, None

    @classmethod
    def check_output(cls, text: str) -> tuple[bool, Optional[str]]:
        """检查 AI 输出内容。"""
        text_lower = text.lower()
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern.lower() in text_lower:
                return False, "AI 输出包含不合规信息，已拦截"
        return True, None
