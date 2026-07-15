import asyncio
import json
from dataclasses import asdict

from cost_runtime import CostAwareController, CostPolicy, LlmRequest


async def main() -> None:
    policy = CostPolicy(
        max_concurrency=1,
        request_timeout=30,
        retries=0,
        max_prompt_tokens=80,
        run_token_budget=200,
        max_output_tokens=64,
    )
    controller = CostAwareController(policy, log_path="logs/budget_guard.jsonl")
    long_context = "这是一段会超过单次 prompt token 上限的上下文。" * 60
    result = await controller.handle(
        LlmRequest(
            request_id="budget-before-call",
            scenario="reject_before_real_call",
            messages=[
                {"role": "system", "content": "关闭 thinking，只输出最终答案。"},
                {"role": "user", "content": long_context},
            ],
        )
    )
    printable = asdict(result)
    printable["answer"] = ""
    print(json.dumps(printable, ensure_ascii=False))
    print("如果 status 是 rejected，说明本次没有必要调用真实模型。")


if __name__ == "__main__":
    asyncio.run(main())
