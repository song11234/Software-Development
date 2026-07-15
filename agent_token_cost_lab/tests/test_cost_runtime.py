import asyncio
import json

from cost_runtime import CostAwareController, CostPolicy, LlmRequest
from real_llm_client import LlmResponse, Usage, estimate_messages_tokens


def make_request(content: str, request_id: str = "test") -> LlmRequest:
    return LlmRequest(
        request_id=request_id,
        scenario="unit_test",
        messages=[
            {"role": "system", "content": "只输出最终答案。"},
            {"role": "user", "content": content},
        ],
    )


async def fake_success(messages: list[dict]) -> LlmResponse:
    prompt_tokens = estimate_messages_tokens(messages)
    completion_tokens = 8
    return LlmResponse(
        content="fake answer",
        model="fake-model",
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated=True,
        ),
        elapsed_ms=1,
    )


def test_prompt_budget_rejects_before_call(tmp_path):
    calls = 0

    async def should_not_call(messages: list[dict]) -> LlmResponse:
        nonlocal calls
        calls += 1
        return await fake_success(messages)

    policy = CostPolicy(max_prompt_tokens=40, run_token_budget=200, max_output_tokens=32)
    controller = CostAwareController(policy, tmp_path / "budget.jsonl", call_func=should_not_call)
    result = asyncio.run(controller.handle(make_request("超长上下文" * 80)))

    assert result.status == "rejected"
    assert result.error_type == "prompt_token_limit_exceeded"
    assert calls == 0


def test_retry_then_success(tmp_path):
    attempts = 0

    async def flaky(messages: list[dict]) -> LlmResponse:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary failure")
        return await fake_success(messages)

    policy = CostPolicy(retries=1, max_prompt_tokens=200, run_token_budget=400)
    controller = CostAwareController(policy, tmp_path / "retry.jsonl", call_func=flaky)
    result = asyncio.run(controller.handle(make_request("请简短回答。"))) 

    assert result.ok is True
    assert result.attempts == 2
    assert attempts == 2


def test_jsonl_log_excludes_prompt_and_answer(tmp_path):
    log_path = tmp_path / "cost.jsonl"
    policy = CostPolicy(max_prompt_tokens=200, run_token_budget=400)
    controller = CostAwareController(policy, log_path, call_func=fake_success)
    result = asyncio.run(controller.handle(make_request("SECRET_PROMPT_SHOULD_NOT_BE_LOGGED")))

    assert result.ok is True
    event = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    serialized = json.dumps(event, ensure_ascii=False)
    assert "SECRET_PROMPT_SHOULD_NOT_BE_LOGGED" not in serialized
    assert "fake answer" not in serialized
    assert event["prompt_tokens"] > 0
    assert event["completion_tokens"] > 0
