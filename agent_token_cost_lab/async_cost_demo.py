import asyncio
import json
import time
from dataclasses import asdict

from cost_runtime import CostPolicy, LlmRequest, run_requests


def build_request(index: int, question: str) -> LlmRequest:
    return LlmRequest(
        request_id=f"async-{index:02d}",
        scenario="small_concurrent_real_calls",
        messages=[
            {"role": "system", "content": "关闭 thinking，只输出最终答案。回答不超过 80 个中文字。"},
            {"role": "user", "content": question},
        ],
    )


async def main() -> None:
    policy = CostPolicy(
        max_concurrency=2,
        request_timeout=60,
        retries=1,
        max_prompt_tokens=500,
        run_token_budget=1200,
        max_output_tokens=96,
    )
    questions = [
        "为什么并发不能降低单次 Token 成本？",
        "为什么重试会放大收费 API 的成本？",
        "为什么长历史对话要做摘要？",
        "为什么要限制 max_tokens？",
    ]
    start = time.perf_counter()
    results = await run_requests(
        [build_request(index, question) for index, question in enumerate(questions, start=1)],
        policy,
        log_path="logs/async_cost.jsonl",
    )
    elapsed = time.perf_counter() - start
    for result in results:
        printable = asdict(result)
        printable["answer"] = result.answer[:80].replace("\n", " ")
        print(json.dumps(printable, ensure_ascii=False))
    print("=" * 80)
    print("elapsed_seconds:", round(elapsed, 3))
    print("total_tokens:", sum(item.total_tokens for item in results))
    print("estimated_cost:", round(sum(item.estimated_cost for item in results), 6))
    print("log_path: logs/async_cost.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
