import asyncio
import inspect
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from real_llm_client import (
    LlmResponse,
    chat_completion,
    estimate_cost,
    estimate_messages_tokens,
)


@dataclass
class CostPolicy:
    """集中保存成本、超时和并发策略，便于实验中调整观察。"""

    max_concurrency: int = 2
    request_timeout: float = 60.0
    retries: int = 1
    retry_base_delay: float = 0.5
    max_prompt_tokens: int = 1200
    run_token_budget: int = 3000
    max_output_tokens: int = 96


@dataclass
class LlmRequest:
    """进入成本运行时的请求协议。messages 遵循 Chat Completions 格式。"""

    request_id: str
    scenario: str
    messages: list[dict]
    metadata: dict = field(default_factory=dict)


@dataclass
class LlmResult:
    """运行时返回给脚本的结果。answer 不写入日志，只供后续步骤串联。"""

    request_id: str
    scenario: str
    ok: bool
    status: str
    model: str
    answer: str
    attempts: int
    elapsed_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_usage: bool
    estimated_cost: float
    error_type: str | None = None

    def to_log_event(self) -> dict:
        """日志只写成本和状态，不写完整 prompt 或完整回答。"""

        event = asdict(self)
        event.pop("answer", None)
        event["answer_chars"] = len(self.answer)
        return event


class JsonlLogger:
    """把每次请求的成本事件写入 JSONL，便于后续统计和排障。"""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def write(self, event: dict) -> None:
        async with self._lock:
            with self.path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(event, ensure_ascii=False) + "\n")


class BudgetLedger:
    """整轮实验预算账本，使用预留 Token 避免并发请求同时冲破预算。"""

    def __init__(self, run_token_budget: int):
        self.run_token_budget = run_token_budget
        self.reserved_tokens = 0
        self._lock = asyncio.Lock()

    async def reserve(self, tokens: int) -> tuple[bool, str | None]:
        async with self._lock:
            if self.reserved_tokens + tokens > self.run_token_budget:
                return False, "run_token_budget_exceeded"
            self.reserved_tokens += tokens
            return True, None


class CostAwareController:
    """统一处理预算预检查、并发、超时、重试和成本日志。"""

    def __init__(
        self,
        policy: CostPolicy,
        log_path: str | Path,
        call_func: Callable[[list[dict]], LlmResponse] | None = None,
    ):
        self.policy = policy
        self.semaphore = asyncio.Semaphore(policy.max_concurrency)
        self.ledger = BudgetLedger(policy.run_token_budget)
        self.logger = JsonlLogger(log_path)
        self.call_func = call_func or self._real_call

    def _real_call(self, messages: list[dict]) -> LlmResponse:
        return chat_completion(messages, timeout=self.policy.request_timeout)

    async def _call_model(self, messages: list[dict]) -> LlmResponse:
        if inspect.iscoroutinefunction(self.call_func):
            return await self.call_func(messages)
        return await asyncio.to_thread(self.call_func, messages)

    async def _reject(self, request: LlmRequest, reason: str, prompt_tokens: int) -> LlmResult:
        result = LlmResult(
            request_id=request.request_id,
            scenario=request.scenario,
            ok=False,
            status="rejected",
            model="",
            answer="",
            attempts=0,
            elapsed_ms=0,
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            total_tokens=prompt_tokens,
            estimated_usage=True,
            estimated_cost=0.0,
            error_type=reason,
        )
        await self.logger.write({"type": "llm_cost_event", **result.to_log_event()})
        return result

    async def handle(self, request: LlmRequest) -> LlmResult:
        start = time.perf_counter()
        prompt_tokens = estimate_messages_tokens(request.messages)
        if prompt_tokens > self.policy.max_prompt_tokens:
            return await self._reject(request, "prompt_token_limit_exceeded", prompt_tokens)

        reserved_tokens = prompt_tokens + self.policy.max_output_tokens
        reserved, reason = await self.ledger.reserve(reserved_tokens)
        if not reserved:
            return await self._reject(request, reason or "run_budget_exceeded", prompt_tokens)

        last_error: str | None = None
        async with self.semaphore:
            for attempt in range(1, self.policy.retries + 2):
                try:
                    response = await asyncio.wait_for(
                        self._call_model(request.messages),
                        timeout=self.policy.request_timeout + 1,
                    )
                    usage = response.usage
                    result = LlmResult(
                        request_id=request.request_id,
                        scenario=request.scenario,
                        ok=True,
                        status="completed",
                        model=response.model,
                        answer=response.content,
                        attempts=attempt,
                        elapsed_ms=int((time.perf_counter() - start) * 1000),
                        prompt_tokens=usage.prompt_tokens,
                        completion_tokens=usage.completion_tokens,
                        total_tokens=usage.total_tokens,
                        estimated_usage=usage.estimated,
                        estimated_cost=estimate_cost(usage.prompt_tokens, usage.completion_tokens),
                    )
                    await self.logger.write({"type": "llm_cost_event", **result.to_log_event()})
                    return result
                except Exception as exc:
                    last_error = type(exc).__name__
                    if attempt <= self.policy.retries:
                        await asyncio.sleep(self.policy.retry_base_delay * attempt)

        result = LlmResult(
            request_id=request.request_id,
            scenario=request.scenario,
            ok=False,
            status="failed",
            model="",
            answer="",
            attempts=self.policy.retries + 1,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            total_tokens=prompt_tokens,
            estimated_usage=True,
            estimated_cost=0.0,
            error_type=last_error,
        )
        await self.logger.write({"type": "llm_cost_event", **result.to_log_event()})
        return result


async def run_requests(
    requests: list[LlmRequest],
    policy: CostPolicy,
    log_path: str | Path,
) -> list[LlmResult]:
    """并发运行一组请求，供实验脚本复用。"""

    controller = CostAwareController(policy, log_path=log_path)
    return await asyncio.gather(*(controller.handle(request) for request in requests))
